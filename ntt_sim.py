from enum import Enum
import os
import subprocess

class Element:
    def __init__(self, ntt_idx, stage, index):
        self.ntt_idx = ntt_idx
        self.stage = stage
        self.index = index

class Task:
    def __init__(self, buffer, input_a, input_b, output_a, output_b):
        self.buffer = buffer
        self.input_a = input_a
        self.input_b = input_b
        self.output_a = output_a
        self.output_b = output_b
    
    def is_ready(self):
        ready_table = self.buffer.ready_table
        input_a = self.input_a
        input_b = self.input_b
        if ready_table[input_a.ntt_idx][input_a.stage][input_a.index] == False:
            return False
        if ready_table[input_b.ntt_idx][input_b.stage][input_b.index] == False:
            return False
        return True
    
    def complete(self):
        ready_table = self.buffer.ready_table
        output_a = self.output_a
        output_b = self.output_b
        ready_table[output_a.ntt_idx][output_a.stage][output_a.index] = True
        ready_table[output_b.ntt_idx][output_b.stage][output_b.index] = True


class ButterflyUnit:
    def __init__(self, bu_id, latency=9):
        self.bu_id = bu_id
        self.latency = latency
        self.queue = []
        self.next_input = None
        self.pipeline = [None] * latency
        self.total_active_cycles = 0
        self.total_cycles = 0
        self.stall_cycles = 0

    def tick(self):
        if self.queue:
            task = self.queue[0]
            if task.is_ready():
                self.next_input = task
                self.total_active_cycles += 1
                self.queue.pop(0)
            else:
                self.stall_cycles += 1

        if self.pipeline[-1]:
            self.pipeline[-1].complete()

        for i in reversed(range(1, self.latency)):
            self.pipeline[i] = self.pipeline[i - 1]
        self.pipeline[0] = self.next_input
        self.next_input = None

        self.total_cycles += 1

class NTT:
    def __init__(self, size, start_idx, stride, mult_stages):
        self.size = size
        self.start_idx = start_idx
        self.stride = stride
        self.ntt_stages = size.bit_length() - 1
        self.mult_stages = mult_stages
        self.total_stages = 1 + self.ntt_stages + self.mult_stages

    def get_addresses(self):
        return [(self.start_idx + i * self.stride) << 5 for i in range(self.size)]

# All NTTs must be same size 
class Chunk:
    def __init__(self, chunk_id, ntts=None):
        self.chunk_id = chunk_id
        self.ntt_size = ntts[0].size if ntts is not None else 0
        self.ntt_num = ntts.len() if ntts is not None else 0
        self.ntt_stages = ntts[0].ntt_stages if ntts is not None else 0
        self.mult_stages = ntts[0].mult_stages if ntts is not None else 0
        self.total_stages = ntts[0].total_stages if ntts is not None else 0
        self.ntts = ntts if ntts is not None else []
        self.read_cycles = 0
        self.write_cycles = 0

    def add_ntt(self, ntt):
        self.ntts.append(ntt)
        if self.ntt_num == 0:
            self.ntt_size = ntt.size
            self.ntt_stages = ntt.ntt_stages
            self.total_stages = ntt.total_stages
            self.total_stages = ntt.total_stages
        self.ntt_num = self.ntt_num + 1


    def generate_trace_file(self, is_write=False):
        os.makedirs("traces", exist_ok=True)
        path = "traces/test.trace"
        with open(path, 'w') as f:
            for ntt in self.ntts:
                for addr in ntt.get_addresses():
                    f.write(f"0x{addr:08x} {'W' if is_write else 'R'}\n")

    def measure_memory_latencies(self):
        def convert_to_accel_cycle(hbm_cycle):
            return (hbm_cycle + 8) // 9  # equivalent to ceil(hbm_cycle / 9)

        # Read latency
        self.generate_trace_file(is_write=False)
        try:
            read_output = subprocess.check_output(["./test"], text=True)
            hbm_read_cycles = int(read_output.strip())
            self.read_cycles = convert_to_accel_cycle(hbm_read_cycles)
        except Exception as e:
            print(f"[Error] Failed to measure read latency: {e}")

        # Write latency
        self.generate_trace_file(is_write=True)
        try:
            write_output = subprocess.check_output(["./test"], text=True)
            hbm_write_cycles = int(write_output.strip())
            self.write_cycles = convert_to_accel_cycle(hbm_write_cycles)
        except Exception as e:
            print(f"[Error] Failed to measure write latency: {e}")

class BufferState(Enum):
    IDLE = 0
    READ = 1
    PROCESSING = 2
    PROCESS_DONE = 3
    WRITE = 4

class Buffer:
    def __init__(self, sim, buffer_id):
        self.sim = sim
        self.id = buffer_id
        self.chunk = None
        self.state = BufferState.IDLE
        self.counter = 0
        self.activate = 0        
        self.ready_table = []
        self.process_done = 0

        self.start_cycle = 0  # 상태 시작 시점 저장
        self.read_start = 0
        self.proc_start = 0
        self.write_start = 0

    def tick(self):
        cycle = self.sim.cycle 

        if self.state == BufferState.IDLE:
            if self.activate:
                self.activate = 0
                self.counter = self.chunk.read_cycles
                self.state = BufferState.READ
                self.read_start = cycle

        elif self.state == BufferState.READ:
            if self.counter == 0:
                self.state = BufferState.PROCESSING
                self.proc_start = cycle
                self.sim.io_turn = 1 - self.id
                self.sim.pending_schedule = 1
                self.sim.pending_schedule_idx = self.id
            self.counter -= 1

        elif self.state == BufferState.PROCESSING:
            if self.process_done:
                if self.sim.io_turn == self.id:
                    self.state = BufferState.WRITE
                    self.counter = self.chunk.write_cycles
                    self.write_start = cycle
                else:
                    self.state = BufferState.PROCESS_DONE

        elif self.state == BufferState.PROCESS_DONE:
            if self.sim.io_turn == self.id:
                self.state = BufferState.WRITE
                self.counter = self.chunk.write_cycles
                self.write_start = cycle

        elif self.state == BufferState.WRITE:
            if self.counter == 0:
                if DEBUG:
                    print(f"[Buffer {self.id} : {self.chunk.chunk_id}] Cycle Report:")
                    print(f"  READ       : {self.proc_start - self.read_start} cycles")
                    print(f"  PROCESSING : {self.write_start - self.proc_start} cycles")
                    print(f"  WRITE      : {cycle - self.write_start} cycles")
                    print(f"  TOTAL      : {cycle - self.read_start} cycles\n")                
                self.state = BufferState.IDLE
                self.chunk = None
            self.counter -= 1

        return None

    def check_process(self):
        for ready_table in self.ready_table:
            for idx in range(self.chunk.ntt_size):
                if not ready_table[-1][idx]:
                    self.process_done = 0
                    return
        self.process_done = 1
        return

class NTTSim:
    def __init__(self, parallel):
        self.cycle = 0
        self.parallel = parallel
        self.BUs = [ButterflyUnit(i) for i in range(parallel)]
        self.buffers = [Buffer(self, 0), Buffer(self, 1)]
        
        self.chunk_queue = []
        self.io_turn = 0
        self.pending_schedule = 0
        self.pending_schedule_idx = 0

    def push_chunk(self, chunk):
        self.chunk_queue.append(chunk)

    def schedule_tasks(self):
        buffer = self.buffers[self.pending_schedule_idx]
        buffer.ready_table.clear()
        ntt_size = buffer.chunk.ntt_size
        ntt_num = buffer.chunk.ntt_num
        ntt_stages = buffer.chunk.ntt_stages
        mult_stages = buffer.chunk.mult_stages
        for ntt_idx in range(ntt_num):
            ready_table = [[False for _ in range(ntt_size)] for _ in range(ntt_stages)]
            for i in range(ntt_size):
                ready_table[0][i] = True
            buffer.ready_table.append(ready_table)

        bu_index = 0
        for stage in range(1, ntt_stages):
            distance = ntt_size >> stage
            group_size = 2 * distance
            num_groups = ntt_size // group_size
            for ntt_idx in range(ntt_num):            
                for group in range(num_groups):
                    for pair in range(distance):
                        index_a = group * group_size + pair
                        index_b = index_a + distance

                        input_a = Element(ntt_idx, stage - 1, index_a)
                        input_b = Element(ntt_idx, stage - 1, index_b)
                        output_a = Element(ntt_idx, stage, index_a)
                        output_b = Element(ntt_idx, stage, index_b)
                        task = Task(buffer, input_a, input_b, output_a, output_b)

                        self.BUs[bu_index % self.parallel].queue.append(task)
                        bu_index += 1
        
        for stage in range(1, mult_stages):
            for ntt_idx in range(ntt_num):
                for element_idx in range(ntt_size):
                    input_a = Element(ntt_idx, ntt_stages + stage - 1, element_idx)
                    input_b = Element(ntt_idx, ntt_stages + stage - 1, element_idx)

                    output_a = Element(ntt_idx, ntt_stages + stage, element_idx)
                    output_b = Element(ntt_idx, ntt_stages + stage, element_idx)
                    task = Task(buffer, input_a, input_b, output_a, output_b)

                    
                    self.BUs[bu_index % self.parallel].queue.append(task)
                    bu_index += 1

    def tick(self):
        for buf in self.buffers:
            if buf.state == BufferState.PROCESSING:
                buf.check_process()

        for bu in self.BUs:
            bu.tick()

        for buf in self.buffers:
            buf.tick()
     
        if(self.pending_schedule):
            self.schedule_tasks()
            self.pending_schedule = 0

        active_buffer = self.buffers[self.io_turn]
        
        if active_buffer.state == BufferState.IDLE and not self.chunk_queue:
            self.io_turn = 1 - self.io_turn

        if active_buffer.state == BufferState.IDLE and self.chunk_queue:
            active_buffer.chunk = self.chunk_queue.pop(0)            
            active_buffer.activate = 1
        



        self.cycle += 1

    def is_done(self):
        return all(buf.state == BufferState.IDLE for buf in self.buffers) and not self.chunk_queue

    def report(self):
        print(f"Total simulation cycles: {self.cycle}")


DEBUG = True

if __name__ == "__main__":
    print("[*] Unified Lazy Chunk Feeding Simulation")

    sim = NTTSim(parallel=8)

    phase = 0
    chunk_id = 0
    ntt_index = 1  # Phase 0: start_idx 1부터

    total_ntts_fine = 512 * 512
    total_ntts_large = 512  # 2^18 NTT 개수

    inner_idx = 0  # 0~511
    current_large_ntt_id = 1

    def create_fine_chunk(chunk_id, ntt_index):
        chunk = Chunk(chunk_id)
        chunk.add_ntt(NTT(
            size=2 ** 9,
            start_idx=ntt_index,
            stride=2 ** 18,
            mult_stages=1 if ntt_index == total_ntts_fine else 0
        ))
        chunk.measure_memory_latencies()
        return chunk

    def create_col_chunk(chunk_id, base_idx, inner_idx):
        chunk = Chunk(chunk_id)
        chunk.add_ntt(NTT(
            size=2 ** 9,
            start_idx=base_idx + inner_idx,
            stride=512,
            mult_stages=1 if (inner_idx == 511 and phase == 1) else 0
        ))
        chunk.measure_memory_latencies()
        return chunk

    def create_row_chunk(chunk_id, base_idx, inner_idx):
        chunk = Chunk(chunk_id)
        chunk.add_ntt(NTT(
            size=2 ** 9,
            start_idx=base_idx + inner_idx * 512,
            stride=1,
            mult_stages=0  # row-wise는 mult_stage 없음
        ))
        chunk.measure_memory_latencies()
        return chunk

    print("[*] Run unified simulation loop")

    while not sim.is_done() or phase < 3:
        if not sim.chunk_queue:
            # Phase 0: fine-grained 2^9 NTTs
            if phase == 0 and ntt_index <= total_ntts_fine:
                chunk = create_fine_chunk(chunk_id, ntt_index)
                sim.push_chunk(chunk)
                chunk_id += 1
                ntt_index += 1

            elif phase == 0:
                phase = 1
                inner_idx = 0
                current_large_ntt_id = 1

            # Phase 1: column-wise first
            elif phase == 1 and current_large_ntt_id <= total_ntts_large:
                chunk = create_col_chunk(chunk_id, current_large_ntt_id, inner_idx)
                sim.push_chunk(chunk)
                chunk_id += 1

                inner_idx += 1
                if inner_idx == 512:
                    inner_idx = 0
                    current_large_ntt_id += 1

            elif phase == 1:
                phase = 2
                inner_idx = 0
                current_large_ntt_id = 1

            # Phase 2: then row-wise (no mult_stage)
            elif phase == 2 and current_large_ntt_id <= total_ntts_large:
                chunk = create_row_chunk(chunk_id, current_large_ntt_id, inner_idx)
                sim.push_chunk(chunk)
                chunk_id += 1

                inner_idx += 1
                if inner_idx == 512:
                    inner_idx = 0
                    current_large_ntt_id += 1

            elif phase == 2:
                phase = 3  # done

        sim.tick()

    sim.report()