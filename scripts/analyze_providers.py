"""Analyze BNetzA operator distribution."""
import csv, collections

CSV_PATH = r"C:\Users\KitCat\Desktop\tesla semi\data\Ladesaeulenregister_BNetzA_2026-04-22.csv"

op_cp = collections.Counter()
op_sites = collections.Counter()
op_classes = collections.defaultdict(lambda: collections.Counter())
state_ops = collections.defaultdict(lambda: collections.Counter())

with open(CSV_PATH, encoding="latin-1") as f:
    for _ in range(10):
        f.readline()
    reader = csv.DictReader(f, delimiter=";")

    for row in reader:
        op = row.get("Betreiber", "").strip()
        state = row.get("Bundesland", "").strip()
        try:
            cp = int(row.get("Anzahl Ladepunkte", "1"))
        except ValueError:
            cp = 1
        try:
            kw = float(row.get("Nennleistung Ladeeinrichtung [kW]", "0").replace(",", "."))
        except ValueError:
            kw = 0
        art = row.get("Art der Ladeeinrichtung", "")

        if kw >= 300:
            cls = "ultra_300"
        elif kw >= 150:
            cls = "hpc_150"
        elif "Schnell" in art or kw >= 50:
            cls = "fast_50"
        else:
            cls = "ac_normal"

        op_cp[op] += cp
        op_sites[op] += 1
        op_classes[op][cls] += cp
        state_ops[state][op] += cp

total_cp = sum(op_cp.values())
total_sites = sum(op_sites.values())
print(f"Total: {total_sites} rows, {total_cp} charge points, {len(op_cp)} unique operators\n")

print("=" * 110)
print("TOP 30 OPERATORS BY CHARGE POINTS")
print("=" * 110)
header = f"{'Operator':<45} {'CP':>6} {'%':>6} {'Cum%':>6}  {'AC':>5} {'Fast':>5} {'HPC':>5} {'Ultra':>5}"
print(header)
print("-" * 110)
cumul = 0
for op, n in op_cp.most_common(30):
    cumul += n
    c = op_classes[op]
    print(f"{op[:44]:<45} {n:>6} {n/total_cp*100:>5.1f}% {cumul/total_cp*100:>5.1f}%  {c['ac_normal']:>5} {c['fast_50']:>5} {c['hpc_150']:>5} {c['ultra_300']:>5}")

print(f"\n{'=' * 110}")
print("PROVIDER CONCENTRATION")
print("=" * 110)
cumul = 0
for i, (op, n) in enumerate(op_cp.most_common(), 1):
    cumul += n
    if cumul / total_cp >= 0.5 and i <= 20:
        print(f"Top {i} operators cover 50%+ ({cumul/total_cp*100:.1f}%)")
    if cumul / total_cp >= 0.8 and i <= 50:
        print(f"Top {i} operators cover 80%+ ({cumul/total_cp*100:.1f}%)")
        break

print(f"\n{'=' * 110}")
print("TOP 5 OPERATORS PER STATE")
print("=" * 110)
for state in sorted(state_ops.keys()):
    if not state:
        continue
    total_state = sum(state_ops[state].values())
    top5 = state_ops[state].most_common(5)
    print(f"\n{state} ({total_state} cp):")
    for op, n in top5:
        print(f"  {n:>5} ({n/total_state*100:4.1f}%)  {op[:60]}")
