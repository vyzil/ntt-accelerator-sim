from ntt_sim import Chunk, NTT, NTTSim

DEBUG = True
DEBUG_BUF_STATE = True


# ==================== Ordinary ====================
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

# ==================== Ordinary ====================



# ==================== HBM-aware ====================

def create_HBMaware_OC_chunk_0(chunk_id, base_index):
    chunk = Chunk(chunk_id)
    for offset in range(16):  # 2^4개의 NTT
        chunk.add_ntt(NTT(
            size=2 ** 9,
            start_idx=base_index + offset,
            stride=2 ** 18,
            mult_stages=5,
            stage_start=0
        ))
    chunk.measure_memory_latencies()
    return chunk

def create_HBMaware_OC_chunk_1(chunk_id, base_index):
    chunk = Chunk(chunk_id)
    for offset in range(16):
        chunk.add_ntt(NTT(
            size=2 ** 9,
            start_idx=base_index + offset,
            stride=1,
            mult_stages=4,
            stage_start=5
        ))
    chunk.measure_memory_latencies()
    return chunk


def run_HBMaware_phase_0_0(sim, chunk_id_start, base_index_start):
    chunk_id = chunk_id_start
    ntt_index = base_index_start
    total_ntts_fine = 512 * 512
    while ntt_index <= total_ntts_fine:
        chunk = create_HBMaware_OC_chunk_0(chunk_id, ntt_index)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        ntt_index += 16  # 2^4개씩 처리
    return chunk_id, ntt_index

def run_HBMaware_phase_0_1(sim, chunk_id_start, base_index_start):
    chunk_id = chunk_id_start
    ntt_index = base_index_start
    total_ntts_fine = 512 * 512
    while ntt_index <= total_ntts_fine:
        chunk = create_HBMaware_OC_chunk_1(chunk_id, ntt_index)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        ntt_index += 16
    return


def test_HBMaware(parallel, phase, sub_phase):
    if phase == 0:
        sim = NTTSim(parallel=parallel)
        print("[*] Run HBM-aware Phase 0 Subphase {}".format(sub_phase))
        if sub_phase == 0:
            run_HBMaware_phase_0_0(sim, chunk_id_start=0, base_index_start=1)
        elif sub_phase == 1:
            run_HBMaware_phase_0_1(sim, chunk_id_start=0, base_index_start=1)
        sim.report()

# ==================== HBM-aware ====================
if __name__ == "__main__":

    parallel = 8
    # test_ordinary(parallel, 0)
    # test_ordinary(parallel, 1)
    # test_ordinary(parallel, 2)
    test_HBMaware(parallel, phase=0, sub_phase=0)
    test_HBMaware(parallel, phase=0, sub_phase=1)