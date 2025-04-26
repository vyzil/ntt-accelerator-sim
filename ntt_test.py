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

# * Use This
# 64-point NTT x 8
def create_HBMaware_OC_0_chunk(chunk_id, ntt_index):
    chunk = Chunk(chunk_id)
    for i in range(2**3):
        chunk.add_ntt(NTT(
            size=2 ** 6,
            start_idx=ntt_index * (2**3) + i,
            stride=(2**18) * (2**3) ,
            mult_stages=0
        ))
    chunk.measure_memory_latencies()
    return chunk

# # 32-point NTT x 16
# def create_HBMaware_OC_0_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for i in range(2**4):
#         chunk.add_ntt(NTT(
#             size=2 ** 5,
#             start_idx=ntt_index * (2**4) + i,
#             stride=(2**18) * (2**4) ,
#             mult_stages=0
#         ))
#     chunk.measure_memory_latencies()
#     return chunk

# # # 16-point NTT x 32
# def create_HBMaware_OC_0_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for i in range(2**5):
#         chunk.add_ntt(NTT(
#             size=2 ** 4,
#             start_idx=ntt_index * (2**5) + i,
#             stride=(2**18) * (2**5) ,
#             mult_stages=0
#         ))
#     chunk.measure_memory_latencies()
#     return chunk



def run_HBMaware_phase_0_0(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    ntt_index = 1
    total_ntts_fine = 512 * 512
    print("[*] Run Phase 0 (Fine NTTs)")
    while ntt_index <= total_ntts_fine:
        chunk = create_HBMaware_OC_0_chunk(chunk_id, ntt_index)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        ntt_index += 1
    sim.report()


# # OC_1 (16-point NTT x 32) : 1 Bank & 2 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**4):
#         for c in range(2):
#             chunk.add_ntt(NTT(
#                 size= 2**4,
#                 start_idx= 2 * (2**4) * (2**18) * r + c + ntt_index * 2,
#                 stride= (2**18),
#                 mult_stages=1
#             ))
#     chunk.measure_memory_latencies()
#     return chunk


# * Use This
# OC_1 (8-point NTT x 64) : 16 channel & 4 row
def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
    chunk = Chunk(chunk_id)
    for r in range(2**4):
        for c in range(4):
            chunk.add_ntt(NTT(
                size= 2**3,
                start_idx= (4) * (2**3) * (2**18) * r + ntt_index * (4) + c,
                stride= (2**18),
                mult_stages=1
            ))
    chunk.measure_memory_latencies()
    return chunk


# # OC_1 (16-point NTT x 32) : 2 Bank & 1 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**4):
#         for c in range(2):
#             chunk.add_ntt(NTT(
#                 size= 2**4,
#                 start_idx= 2 * (2**4) * (2**18) * r + (2**5) * (c + 2*(ntt_index // (2**5))) + (ntt_index % (2**5)),
#                 stride= (2**18),
#                 mult_stages=1
#             ))
#     chunk.measure_memory_latencies()
#     return chunk

# # OC_1 (16-point NTT x 32) : 1 Bank & 4 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**3):
#         for c in range(4):
#             chunk.add_ntt(NTT(
#                 size= 2**4,
#                 start_idx= 4 * (2**4) * (2**18) * r + c + ntt_index * 4,
#                 stride= (2**18),
#                 mult_stages=1
#             ))
#     chunk.measure_memory_latencies()
#     return chunk

# # OC_1 (16-point NTT x 32) : 2 Bank & 2 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**3):
#         for c in range(4):
#             chunk.add_ntt(NTT(
#                 size= 2**4,
#                 start_idx= 4 * (2**4) * (2**18) * r + (2**5) * ((c//2) + 2*(ntt_index // (2**5))) + ((c % 2) + ntt_index % (2**5)),
#                 stride= (2**18),
#                 mult_stages=1
#             ))
#     chunk.measure_memory_latencies()
#     return chunk

# # OC_1 (16-point NTT x 32) : 4 Bank & 1 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**3):
#         for c in range(4):
#             chunk.add_ntt(NTT(
#                 size= 2**4,
#                 start_idx= 4 * (2**4) * (2**18) * r + (2**5) * (c + 4*(ntt_index // (2**5))) + (ntt_index % (2**5)),
#                 stride= (2**18),
#                 mult_stages=1
#             ))
#     chunk.measure_memory_latencies()
#     return chunk


# # OC_1 (32-point NTT x 16) : 16 Channel & 1 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**4):
#         chunk.add_ntt(NTT(
#             size= 2**5,
#             start_idx= (2 ** 18) * (2 ** 5) * r + ntt_index,
#             stride= (2**18),
#             mult_stages=1
#         ))
#     chunk.measure_memory_latencies()
#     return chunk

# # OC_1 (32-point NTT x 16) : 1 Channel & 16 Row Hit
# def create_HBMaware_OC_1_chunk(chunk_id, ntt_index):
#     chunk = Chunk(chunk_id)
#     for r in range(2**4):
#         chunk.add_ntt(NTT(
#             size= 2**5,
#             start_idx= (2**4)*ntt_index + r,
#             stride= (2**18),
#             mult_stages=1
#         ))
#     chunk.measure_memory_latencies()
#     return chunk

def run_HBMaware_phase_0_1(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    ntt_index = 1
    total_ntts_fine = 512 * 512
    print("[*] Run Phase 0 (Fine NTTs)")
    while ntt_index <= total_ntts_fine:
        chunk = create_HBMaware_OC_1_chunk(chunk_id, ntt_index)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        ntt_index += 1
    sim.report()



# # # IC_0 (16CH x 8-point NTT x 4) : 16 Channel & 4 Row Hit
# def create_HBMaware_IC_0_chunk(chunk_id, outer_idx, inner_idx):
#     chunk = Chunk(chunk_id)
#     for r in range(2**4):
#         for c in range(4):
#             chunk.add_ntt(NTT(
#                 size=2 ** 3,
#                 start_idx= (32*r + outer_idx) * (2**18) + inner_idx * 4 + c ,
#                 stride=(2**9) * (2**3) ,
#                 mult_stages=0
#             ))
#     chunk.measure_memory_latencies()
#     return chunk

# # IC_0 (16CH x 16-point NTT x 2) : 16 Channel & 2 Row Hit
def create_HBMaware_IC_0_chunk(chunk_id, outer_idx, inner_idx):
    chunk = Chunk(chunk_id)
    for r in range(2**4):
        for c in range(2):
            chunk.add_ntt(NTT(
                size=2 ** 4,
                start_idx= (32*r + outer_idx) * (2**18) + inner_idx * 4 + c ,
                stride=(2**9) * (2**4) ,
                mult_stages=0
            ))
    chunk.measure_memory_latencies()
    return chunk



def run_HBMaware_phase_1_0(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    outer_idx = 0
    inner_idx = 0
    total_ntts_large = 32
    print("[*] Run Phase 1 (Column-wise)")
    while outer_idx <= total_ntts_large:
        chunk = create_HBMaware_IC_0_chunk(chunk_id, outer_idx, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512*16:
            inner_idx = 0
            outer_idx += 1
    sim.report()



# # # IC_1 (16CH x 32-point NTT) : 16 Channel & 4 Row Hit
# def create_HBMaware_IC_1_chunk(chunk_id, outer_idx, inner_idx):
#     chunk = Chunk(chunk_id)
#     for r in range(2**3):
#         chunk.add_ntt(NTT(
#             size=2 ** 5,
#             start_idx= (32*r + outer_idx) * (2**18) + (2**9) * (2**5) * (inner_idx // 512) + (inner_idx % 512),
#             stride=(2**9),
#             mult_stages=1
#         ))
#     chunk.measure_memory_latencies()
#     return chunk


# # 16 CH
# def run_HBMaware_phase_1_1(parallel):
#     sim = NTTSim(parallel=parallel)
#     chunk_id = 0
#     outer_idx = 0
#     inner_idx = 0
#     total_ntts_large = 32
#     print("[*] Run Phase 1 (Column-wise)")
#     while outer_idx <= total_ntts_large:
#         chunk = create_HBMaware_IC_1_chunk(chunk_id, outer_idx, inner_idx)
#         sim.push_chunk(chunk)
#         while sim.chunk_queue:
#             sim.tick()
#         chunk_id += 1
#         inner_idx += 1
#         if inner_idx == 512*16:
#             inner_idx = 0
#             outer_idx += 1
#     sim.report()


# # IC_1 (8CH x 64-point NTT) : 8 Channel & 1 Row Hit
def create_HBMaware_IC_1_chunk(chunk_id, outer_idx, inner_idx):
    chunk = Chunk(chunk_id)
    for r in range(2**3):
        chunk.add_ntt(NTT(
            size=2 ** 6,
            start_idx= (64*r + outer_idx) * (2**18) + (2**9) * (2**6) * (inner_idx // 512) + (inner_idx % 512),
            stride=(2**9),
            mult_stages=1
        ))
    chunk.measure_memory_latencies()
    return chunk

# 8 CH
def run_HBMaware_phase_1_1(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    outer_idx = 0
    inner_idx = 0
    total_ntts_large = 64
    print("[*] Run Phase 1 (Column-wise)")
    while outer_idx <= total_ntts_large:
        chunk = create_HBMaware_IC_1_chunk(chunk_id, outer_idx, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512*8:
            inner_idx = 0
            outer_idx += 1
    sim.report()


# # 32-point NTT
# def create_HBMaware_IR_0_chunk(chunk_id, outer_idx, inner_idx):
#     chunk = Chunk(chunk_id)
#     for r in range(2**4):
#         chunk.add_ntt(NTT(
#             size=2**5,
#             start_idx= (32*r + outer_idx) * (2**18) + (2**9) * (inner_idx // (2**4)) +  (inner_idx % (2**4)),
#             stride= (2**4) ,
#             mult_stages=0
#         ))
#     chunk.measure_memory_latencies()
#     return chunk

# 16-point NTT x 2
def create_HBMaware_IR_0_chunk(chunk_id, outer_idx, inner_idx):
    chunk = Chunk(chunk_id)
    for r in range(2**4):
        for c in range(2):
            chunk.add_ntt(NTT(
                size=2**4,
                start_idx= (32*r + outer_idx) * (2**18) + (2**9) * (inner_idx // (2**4)) +  2 * (inner_idx % (2**4)) + c,
                stride= (2**4),
                mult_stages=0
            ))
    chunk.measure_memory_latencies()
    return chunk

# 16 CH
def run_HBMaware_phase_2_0(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    outer_idx = 0
    inner_idx = 0
    total_ntts_large = 32
    print("[*] Run Phase 1 (Column-wise)")
    while outer_idx <= total_ntts_large:
        chunk = create_HBMaware_IR_0_chunk(chunk_id, outer_idx, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512*16:
            inner_idx = 0
            outer_idx += 1
    sim.report()


# # 16-point NTT x 2
# def create_HBMaware_IR_1_chunk(chunk_id, outer_idx, inner_idx):
#     chunk = Chunk(chunk_id)
#     for r in range(2**5):
#         for c in range(2):
#             chunk.add_ntt(NTT(
#                 size=2**4,
#                 start_idx= (32*r + outer_idx) * (2**18) + (2**4) * c + (2**5) * inner_idx,
#                 stride= 1 ,
#                 mult_stages=1
#             ))
#     chunk.measure_memory_latencies()
#     return chunk

# 32-point NTT x 1
def create_HBMaware_IR_1_chunk(chunk_id, outer_idx, inner_idx):
    chunk = Chunk(chunk_id)
    for r in range(2**3):
        chunk.add_ntt(NTT(
            size=2**5,
            start_idx= (32*r + outer_idx) + (2**9) * (inner_idx // (2**4)) + (inner_idx % (2**4)) ,
            stride= 1 ,
            mult_stages=1
        ))
    chunk.measure_memory_latencies()
    return chunk



    # 16 CH
def run_HBMaware_phase_2_1(parallel):
    sim = NTTSim(parallel=parallel)
    chunk_id = 0
    outer_idx = 0
    inner_idx = 0
    total_ntts_large = 32
    print("[*] Run Phase 1 (Column-wise)")
    while outer_idx <= total_ntts_large:
        chunk = create_HBMaware_IR_1_chunk(chunk_id, outer_idx, inner_idx)
        sim.push_chunk(chunk)
        while sim.chunk_queue:
            sim.tick()
        chunk_id += 1
        inner_idx += 1
        if inner_idx == 512*16:
            inner_idx = 0
            outer_idx += 1
    sim.report()


# ==================== HBM-aware ====================
if __name__ == "__main__":

    parallel = 16

    # # No subtile
    # test_ordinary(parallel, 0)
    # test_ordinary(parallel, 1)
    # test_ordinary(parallel, 2)

    # # Subtile
    # run_HBMaware_phase_0_0(parallel=parallel)
    # run_HBMaware_phase_0_1(parallel=parallel)
    # run_HBMaware_phase_1_0(parallel=parallel)
    run_HBMaware_phase_1_1(parallel=parallel)
    # run_HBMaware_phase_2_0(parallel=parallel)
    # run_HBMaware_phase_2_1(parallel=parallel)