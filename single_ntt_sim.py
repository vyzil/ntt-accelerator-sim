class Element:
    def __init__(self, ntt_id, stage, index):
        self.ntt_id = ntt_id
        self.stage = stage
        self.index = index

class Task:
    def __init__(self, input_a, input_b, output_a, output_b):
        self.input_a = input_a
        self.input_b = input_b
        self.output_a = output_a
        self.output_b = output_b

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
        self.ready_table = None

    def set_ready_table(self, ready_table):
        self.ready_table = ready_table

    def is_ready(self, element):
        return self.ready_table[element.ntt_id][element.stage][element.index]

    def tick(self):
        # 1. issue 준비
        if self.queue:
            task = self.queue[0]
            if self.is_ready(task.input_a) and self.is_ready(task.input_b):
                self.next_input = task
                self.total_active_cycles += 1
                self.queue.pop(0)
            else:
                self.stall_cycles += 1  # ← input ready 안됨 → stall

        # 2. output 처리
        completed = self.pipeline[-1]
        if completed:
            out_a = completed.output_a
            out_b = completed.output_b
            self.ready_table[out_a.ntt_id][out_a.stage][out_a.index] = True
            self.ready_table[out_b.ntt_id][out_b.stage][out_b.index] = True

        # 3. pipeline shift
        for i in reversed(range(1, self.latency)):
            self.pipeline[i] = self.pipeline[i - 1]
        self.pipeline[0] = self.next_input
        self.next_input = None

        self.total_cycles += 1


class NTTSim:
    def __init__(self, size, num, parallel, mult_stage=0):
        self.size = size
        self.num = num
        self.parallel = parallel
        self.mult_stage = mult_stage
        self.total_stages = size.bit_length() - 1
        self.cycles = 0
        self.tasks = []

        # Ready table: [ntt_id][stage][index]
        self.ready_table = [[[False for _ in range(size)]
                             for _ in range(self.total_stages + 1 + mult_stage)]
                             for _ in range(num)]

        # Initialize BUs
        self.BUs = [ButterflyUnit(i) for i in range(parallel)]
        for bu in self.BUs:
            bu.set_ready_table(self.ready_table)

        # 모든 input은 stage 0에서 ready로 설정
        for ntt_id in range(num):
            for i in range(size):
                self.ready_table[ntt_id][0][i] = True

    def check_valid_parameters(self):
        min_tasks_per_stage = self.size // 2
        if min_tasks_per_stage < self.parallel:
            print(f"[Error] N/2 = {min_tasks_per_stage} tasks per stage < {self.parallel} BUs.")
            return False
        return True

    def schedule(self):
        bu_index = 0  # round-robin BU index

        for stage in range(1, self.total_stages + 1):  # stage 1부터 시작
            distance = self.size >> stage
            group_size = 2 * distance
            num_groups = self.size // group_size

            for ntt_id in range(self.num):
                for group in range(num_groups):
                    for pair in range(distance):
                        index_a = group * group_size + pair
                        index_b = index_a + distance

                        input_a = Element(ntt_id, stage - 1, index_a)
                        input_b = Element(ntt_id, stage - 1, index_b)
                        output_a = Element(ntt_id, stage, index_a)
                        output_b = Element(ntt_id, stage, index_b)
                        task = Task(input_a, input_b, output_a, output_b)

                        self.BUs[bu_index % self.parallel].queue.append(task)
                        bu_index += 1


    def is_ready(self, element):
        return self.ready_table[element.ntt_id][element.stage][element.index]


    def run(self):
        # if not self.check_valid_parameters():
        #     return

        while not self.finished():
            for bu in self.BUs:
                bu.tick()
            self.cycles += 1


    def finished(self):
        return all(not bu.queue and all(stage is None for stage in bu.pipeline)
                   for bu in self.BUs)


    def report(self):
        print(f"Total simulation cycles: {self.cycles}")
        for bu in self.BUs:
            utilization = bu.total_active_cycles / bu.total_cycles if bu.total_cycles > 0 else 0.0
            stall_ratio = bu.stall_cycles / bu.total_cycles if bu.total_cycles > 0 else 0.0
            print(f"BU{bu.bu_id}: Utilization = {utilization:.2%}, Stall = {stall_ratio:.2%} "
                f"({bu.total_active_cycles}/{bu.total_cycles}, stalled {bu.stall_cycles} cycles)")

