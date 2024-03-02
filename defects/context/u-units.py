from ...context import units as module

def test_bytes_metric(test):
	n, o, l = module.metric(999)
	test/o == 0
	test/n == 999.0
	test/l == ''

def test_bytes_iec(test):
	n, o, l = module.iec(1023)
	test/o == 0
	test/n == 1023.0
	test/l == ''

def test_kilobytes(test):
	n, o, l = module.metric(1000 ** 1)
	test/o == 1
	test/n == 1.0
	test/l == 'kilo'

def test_gigabytes(test):
	n, o, l = module.metric(1000 ** 3)
	test/o == 3
	test/n == 1.0
	test/l == 'giga'

def test_formats(test):
	test/module.format_iec(1024) == "1.000 KiB"
	test/module.format_iec(1024 * 100) == "100.0 KiB"

	test/module.format_metric(1000 * 100) == "100.0 KB"
	test/module.format_metric(1000 * 1000) == "1.000 MB"

def test_negative_sizes(test):
	test/module.format_metric(-1000 * 100) == "-100.0 KB"

def test_final_order(test):
	nbytes = (1000 ** 8) * 2000
	test/module.format_metric(nbytes) == "2e+03 YB"
