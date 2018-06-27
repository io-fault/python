"""
# Interpret a fault.text encoded data structure.
# &protocol contains the supported types.
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

def _factor_field_i(obj):
	t = obj[0]
	if t == 'paragraph':
		# Linked identifier.
		first = document.paragraph_only(obj)
		if first is None:
			return document.paragraph_as_string(obj)
		else:
			return document.interpret_paragraph_single(first)

def _requirement_i(obj):
	for t in obj:
		if t[0] in {'set', 'sequence'}:
			for i in t[1]:
				yield document.paragraph_as_string(i[1][0])

def _context_data(section):
	# Currently limited to sections only containing one admonition.
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

	# Trim
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

def factor(data):
	main_dict = {
		e[1][0][1][0]: (e[1][1][1]) for e in data[0]
	}
	for k in ('type', 'domain'):
		a = main_dict[k]
		main_dict[k] = _factor_field_i(a[0])

	reqs = main_dict.get('integrals')
	if reqs is not None:
		main_dict['integrals'] = set(_requirement_i(reqs))

	return main_dict

protocol = {
	"http://if.fault.io/project": project,
	"http://if.fault.io/factor": factor
}

def parse(text):
	try:
		tree = list(libtext.parse(text))
		context, main = _context_data(tree[0][1])
		si = protocol[context['protocol'][0][-1]]
		struct = si(main.pop('dictionary'))
	except Exception as err:
		raise ValueError("unrecognized text structure") from err

	return context, struct

if __name__ == '__main__':
	import sys
	import pprint
	pprint.pprint(parse(sys.stdin.read()))
