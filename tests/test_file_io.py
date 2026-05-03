"""Fayl I/O testləri."""


def test_write_read(tmp_path, run):
    p = tmp_path / "out.txt"
    src = f"""
write_file("{p}", "salam\\ndive\\n")
print(read_file("{p}"))
"""
    out = run(src)
    assert "salam" in out and "dive" in out


def test_open_close(tmp_path, run):
    p = tmp_path / "data.txt"
    src = f"""
f = open("{p}", "w")
f.write("birinci\\n")
f.write("ikinci\\n")
f.close()

f = open("{p}", "r")
xt = f.read()
f.close()
print(xt)
"""
    out = run(src)
    assert "birinci" in out and "ikinci" in out


def test_append(tmp_path, run):
    p = tmp_path / "log.txt"
    src = f"""
write_file("{p}", "1\\n")
append_file("{p}", "2\\n")
append_file("{p}", "3\\n")
print(read_file("{p}"))
"""
    out = run(src)
    assert out.strip().split("\n") == ["1", "2", "3"]
