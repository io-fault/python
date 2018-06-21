"""
# Interpret a fault.text encoded data structure.
"""
from . import document
from . import library as libtext

def _project_interpret(obj):
	t = obj[0]
	if t == 'paragraph':
		first = document.paragraph_only(obj)
		if first is None:
			return document.paragraph_as_string(obj)
		else:
			return document.interpret_paragraph_single(first)
	elif t == 'set':
		c = obj[1]
		c = [document.paragraph_first(x[1][0]) for x in c]
		r = dict([(x[-1].get('cast'), (x[1][0])) for x in c])
		return r

def _context_data(section):
	a = section
	k = dict([(k, (v, p)) for k, v, p in a])
	context_admonition = k.pop('admonition', None)
	ctx = None

	if context_admonition:
		if context_admonition[1]['type'] == 'CONTEXT':
			ctx = document.context(context_admonition)
			for x in ctx:
				v = ctx[x]
				if v[0] == 'paragraph':
					ctx[x] = document.export(v[1])
				elif v[0] == 'syntax':
					ctx[x] = document.concatenate(v)

	return ctx, k

def project(data):
	main_dict = {
		e[1][0][1][0]: (e[1][1][1][0]) for e in data[0]
	}
	abs_para = main_dict.pop('abstract')[1]

	for i in range(len(abs_para)):
		if abs_para[i]:
			break
	del abs_para[:i]
	for i in range(len(abs_para)-1, 0, -1):
		if abs_para[i]:
			break
	del abs_para[i+1:]

	main_dict = {k:_project_interpret(v) for k,v in main_dict.items()}
	main_dict['abstract'] = document.export(abs_para)

	return main_dict

protocol = {
	'http://if.fault.io/project': project
}

def parse(text):
	tree = list(libtext.parse(text))
	context, main = _context_data(tree[0][1])
	si = protocol[context['protocol'][0][-1]]
	return context, si(main.pop('dictionary'))

if __name__ == '__main__':
	import sys
	import pprint
	pprint.pprint(parse(sys.stdin.read()))
