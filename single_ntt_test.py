from single_ntt_sim import NTTSim

def test_singleNTT(size, num, parallel, mult_stage=0):
    print(f"\n=== NTT_ACC({size}, {num}, {parallel}, {mult_stage}) ===")
    sim = NTTSim(size, num, parallel, mult_stage)
    sim.schedule()
    sim.run()
    sim.report()

def test_BU_singleNTT():
    sizes = [2 ** k for k in range(4, 15)]  # NTT size: 16 ~ 16384
    bu_counts = [4, 8, 16, 32]
    num = 1
    mult_stage = 0
    col_width = 10  # 고정 너비 설정

    results = {}  # (bu, size) -> (cycle, stall)

    # 시뮬레이션 실행
    for bu in bu_counts:
        for size in sizes:
            sim = NTTSim(size, num, bu, mult_stage)
            sim.schedule()
            sim.run()
            cycle = sim.cycles
            stall = sim.BUs[0].stall_cycles
            results[(bu, size)] = (cycle, stall)

    # 헤더 출력
    header = ["BU \\ NTT".ljust(col_width)] + [str(s).ljust(col_width) for s in sizes]
    print("".join(header))
    print("-" * (col_width * len(header)))

    # 데이터 출력
    for bu in bu_counts:
        row = [str(bu).ljust(col_width)]
        for size in sizes:
            cycle, stall = results[(bu, size)]
            cell = f"{cycle}({stall})"
            row.append(cell.ljust(col_width))
        print("".join(row))

        
def test_parallel_by_element(element_count=512):
    bu_counts = [4, 8, 16, 32]
    col_width = 12
    results = {}
    combinations = []

    for size in range(2, element_count + 1):
        if element_count % size == 0:
            num = element_count // size
            if (size & (size - 1)) == 0 and (num & (num - 1)) == 0:
                combinations.append((size, num))

    for size, num in combinations:
        results[(size, num)] = {}
        for bu in bu_counts:
            sim = NTTSim(size, num, bu)
            sim.schedule()
            sim.run()
            cycle = sim.cycles
            stall = sim.BUs[0].stall_cycles
            results[(size, num)][bu] = (cycle, stall)

    # 터미널 출력
    header = ["(size,num)".ljust(col_width)] + [f"BU={b}".ljust(col_width) for b in bu_counts]
    print("".join(header))
    print("-" * (len(header) * col_width))

    for key in combinations:
        row = [f"{key}".ljust(col_width)]
        for bu in bu_counts:
            cycle, stall = results[key][bu]
            row.append(f"{cycle}({stall})".ljust(col_width))
        print("".join(row))

if __name__ == "__main__":
    # test_singleNTT(512, 1, 8)
    test_BU_singleNTT()
    # test_parallel_by_element(512)