from ntt_sim import Chunk, NTT, NTTSim

DEBUG = True
DEBUG_BUF_STATE = True

def create_ord_OC_chunk(chunk_id, ntt_index):
    chunk = Chunk(chunk_id)
    chunk.add_ntt(NTT(
        size=2 ** 9,
        start_idx=ntt_index,
        stride=2 ** 18,
        mult_stages=1
    ))
    chunk.measure_memory_latencies()
    return chunk

def create_ord_IC_chunk(chunk_id, base_idx, inner_idx):
    chunk = Chunk(chunk_id)
    chunk.add_ntt(NTT(
        size=2 ** 9,
        start_idx= 512 * 512 * base_idx + inner_idx,
        stride=512,
        mult_stages=1
    ))
    chunk.measure_memory_latencies()
    return chunk

def create_ord_IR_chunk(chunk_id, base_idx, inner_idx):
    chunk = Chunk(chunk_id)
    chunk.add_ntt(NTT(
        size=2 ** 9,
        start_idx=base_idx + inner_idx * 512,
        stride=1,
        mult_stages=0
    ))
    chunk.measure_memory_latencies()
    return chunk

def run_ord_phase_0(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    ntt_index = 1
    total_ntts_fine = 512 * 512
    print("[*] Run Phase 0 (Fine NTTs)")
    while ntt_index <= total_ntts_fine:
        chunk = create_ord_OC_chunk(chunk_id, ntt_index)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        ntt_index += 1
    sim.report()

def run_ord_phase_1(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    inner_idx = 0
    current_large_ntt_id = 1
    total_ntts_large = 512
    print("[*] Run Phase 1 (Column-wise)")
    while current_large_ntt_id <= total_ntts_large:
        chunk = create_ord_IC_chunk(chunk_id, current_large_ntt_id, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512:
            inner_idx = 0
            current_large_ntt_id += 1
    sim.report()

def run_ord_phase_2(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    inner_idx = 0
    current_large_ntt_id = 1
    total_ntts_large = 512
    print("[*] Run Phase 2 (Row-wise)")
    while current_large_ntt_id <= total_ntts_large:
        chunk = create_ord_IR_chunk(chunk_id, current_large_ntt_id, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512:
            inner_idx = 0
            current_large_ntt_id += 1
    sim.report()

def test_ordinary(parallel, phase):
    func = [run_ord_phase_0, run_ord_phase_1, run_ord_phase_2]
    func[phase](parallel=parallel)

def test_HBMaware(parallel, phase, sub_phase):
    return

if __name__ == "__main__":
    # test_ordinary(8, 2)