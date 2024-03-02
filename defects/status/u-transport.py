from ...status import transport as module

def test_isolate_empty(test):
	test/list(module.isolate("")) == []

def test_isolate_one(test):
	test/list(module.isolate("sole: content")) == [["sole: content"]]

def test_isolate_pair(test):
	lines = "\n".join([
		"key-1: value-1",
		"key-2: value-2",
	])

	test/list(module.isolate(lines)) == [["key-1: value-1"], ["key-2: value-2"]]

def test_sequence(test):
	data = [
		('k1', ['v1'])
	]
	test/module.sequence(data) == "k1: v1\n"
