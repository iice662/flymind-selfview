import sys, os
sys.path.insert(0, os.getcwd())
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
data = f.read(300000)
magic = bytes.fromhex("28b52ffd")
pos = data.find(magic)
print("zstd magic occurrences in first 300KB:")
cnt = 0
while pos != -1 and cnt < 10:
    print("   at", pos, "context:", data[max(0,pos-6):pos+8].hex())
    pos = data.find(magic, pos+1)
    cnt += 1
print("total:", cnt)
print("first 32 bytes of file:", data[:32].hex())
