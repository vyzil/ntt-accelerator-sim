from ntt_sim import Chunk, NTT, NTTSim

DEBUG = True
DEBUG_BUF_STATE = True

def create_fine_chunk(chunk_id, ntt_index):
    chunk = Chunk(chunk_id)
    chunk.add_ntt(NTT(
        size=2 ** 9,
        start_idx=ntt_index,
        stride=2 ** 18,
        mult_stages=1
    ))
    chunk.measure_memory_latencies()
    return chunk

def create_col_chunk(chunk_id, base_idx, inner_idx):
    chunk = Chunk(chunk_id)
    chunk.add_ntt(NTT(
        size=2 ** 9,
        start_idx=base_idx + inner_idx,
        stride=512,
        mult_stages=1 if (inner_idx == 511) else 0
    ))
    chunk.measure_memory_latencies()
    return chunk

def create_row_chunk(chunk_id, base_idx, inner_idx):
    chunk = Chunk(chunk_id)
    chunk.add_ntt(NTT(
        size=2 ** 9,
        start_idx=base_idx + inner_idx * 512,
        stride=1,
        mult_stages=0
    ))
    chunk.measure_memory_latencies()
    return chunk

def run_phase_0(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    ntt_index = 1
    total_ntts_fine = 512 * 512
    print("[*] Run Phase 0 (Fine NTTs)")
    while ntt_index <= total_ntts_fine:
        chunk = create_fine_chunk(chunk_id, ntt_index)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        ntt_index += 1
    sim.report()

def run_phase_1(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    inner_idx = 0
    current_large_ntt_id = 1
    total_ntts_large = 512
    print("[*] Run Phase 1 (Column-wise)")
    while current_large_ntt_id <= total_ntts_large:
        chunk = create_col_chunk(chunk_id, current_large_ntt_id, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512:
            inner_idx = 0
            current_large_ntt_id += 1
    sim.report()

def run_phase_2(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    inner_idx = 0
    current_large_ntt_id = 1
    total_ntts_large = 512
    print("[*] Run Phase 2 (Row-wise)")
    while current_large_ntt_id <= total_ntts_large:
        chunk = create_row_chunk(chunk_id, current_large_ntt_id, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512:
            inner_idx = 0
            current_large_ntt_id += 1
    sim.report()

if __name__ == "__main__":
    print("[*] Unified Lazy Chunk Feeding Simulation")
    parallel = 8
    run_phase_0(parallel=8)
    # run_phase_1(parallel=8)
    # run_phase_2(parallel=8)
