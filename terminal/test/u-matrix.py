"""
# Most of the tests here are sanity tests primarily checking to make sure exceptions aren't
# raised from good parameters.
"""
from .. import matrix as module
types = module.types

def test_Type(test):
	"""
	# - &module.Type
	"""
	dt = module.Type('utf-8')
	test/dt.encoding == 'utf-8'
	test/dt.csi(b'm', b'0') == b"\x1b[0m"
	test/LookupError ^ (lambda: module.Type("no-such-encoding"))

def test_Type_transition(test):
	"""
	# - &module.Type.transition_render_parameters
	# - &module.Type.select_transition
	"""
	t = module.Type('utf-8')
	transition = t.transition_render_parameters
	notraits = types.NoTraits

	leading = (notraits, 0, 0, 0)
	following = (notraits, 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[38;2;0;0;1m'

	# No transition.
	leading = (notraits, 1, 0, 0)
	following = (notraits, 1, 0, 0)
	test/(transition(leading, following)) == b''

	# elimation (underline)
	leading = (types.Traits.construct('underline'), 1, 0, 0)
	following = (notraits, 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[24m'

	# transition in (underline)
	leading = (notraits, 1, 0, 0)
	following = (types.Traits.construct('underline'), 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[4m'

	# transition in underline from double
	leading = (types.Traits.construct('double-underline'), 1, 0, 0)
	following = (types.Traits.construct('underline'), 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[24;4m'

def test_Type_linecolor_transition(test):
	"""
	# - &module.Type.transition_render_parameters
	# - &module.Type.select_transition
	"""
	t = module.Type('utf-8')
	transition = t.transition_render_parameters

	rp = types.RenderParameters.from_colors(0, 0)
	lc24 = rp.update(linecolor=0)
	lc8 = rp.update(linecolor=-1)

	# 24-bit
	test/(transition(rp, lc24)) == b'\x1b[58;2;0;0;0m'

	# No transition needed.
	test/(transition(lc24, lc24)) == b''

	# Reset
	test/(transition(lc24, rp)) == b'\x1b[59m'

	# 8-bit, xterm-256
	test/(transition(rp, lc8)) == b'\x1b[58;5;0m'

	# No transition needed.
	test/(transition(lc8, lc8)) == b''

	# Reset
	test/(transition(lc8, rp)) == b'\x1b[59m'

def test_Type_replicate_parameters(test):
	"""
	# - &module.Type.replicate

	# Validate field placement in the constructed sequence.
	"""
	t = module.Type('utf-8')
	r = t.replicate((2, 1), (4, 3), (6, 5))
	test/r == b"\x1b[1;2;3;4;1;5;6;1$v"

def test_Type_erase_parameters(test):
	"""
	# - &module.Type.erase

	# Validate field placement in the constructed sequence.
	"""
	t = module.Type('utf-8')
	r = t.erase((2, 1), (4, 3))
	test/r == b"\x1b[1;2;3;4$z"

def test_Context_erase_zero(test):
	"""
	# - &module.Type.erase

	# Validate empty string result when zero.
	# Emulators will not respect the value.
	"""
	ctx = module.Screen()
	test/ctx.erase(0) == b''

def test_Context_render_transitions(test):
	"""
	# - &module.Context.render

	# Validates that &module.Context.transition is properly applied.
	"""
	s = module.Screen()

	# Underline to bold.
	ph = types.Phrase.construct([
		("Simple", s.Traits.construct('underline'), -1024, -1024, -1024),
		(" ", s.Traits.construct('bold'), -1024, -1024, -1024),
		("phrase.", s.Traits.construct('bold'), -1024, -1024, -1024),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24;1m', b' ', b'', b'phrase.']

	# Underline to far bold.
	ph = types.Phrase.construct([
		("Simple", s.Traits.construct('underline'), -1024, -1024, -1024),
		(" ", s.Traits.construct('underline'), -1024, -1024, -1024),
		("phrase.", s.Traits.construct('bold'), -1024, -1024, -1024),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'', b' ', b'\x1b[24;1m', b'phrase.']

	# New text.
	ph = types.Phrase.construct([
		("Simple", s.Traits.construct('underline'), -1024, -1024, -1024),
		(" ", s.Traits.none(), -1024, -1024, -1024),
		("phrase.", s.Traits.construct('bold'), -1024, -1024, -1024),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24m', b' ', b'\x1b[1m', b'phrase.']

def test_Context_stored_colors(test):
	"""
	# - &module.Context.context_set_text_color
	# - &module.Context.context_set_cell_color
	# - &module.Context.context_set_line_color
	# - &module.Context.set_text_color
	# - &module.Context.set_cell_color
	# - &module.Context.set_line_color
	# - &module.Context.reset_colors
	# - &module.Context.render
	"""
	s = module.Screen()
	test/s.reset_colors() == b'\x1b[39;49;59m'

	test/s.context_set_cell_color(-513)
	test/s.context_set_text_color(-513)
	test/s.context_set_line_color(-8) # Only xterm-256 and 24-bit colors.

	test/s.reset_colors() == b'\x1b[31;41;58;5;7m'

	# Check that render considers the default; transition filters.
	ph = s.Phrase.construct([
		("Simple", types.Traits(0), -513, -513, -8),
		(" ", types.Traits(0), -513, -513, -8),
		("phrase.", types.Traits(0), -513, -513, -8),
	])
	rph = list(s.render(ph))
	test/rph == [b'', b'Simple', b'', b' ', b'', b'phrase.']

def test_Screen_methods(test):
	"""
	# - &module.Screen

	# Check sanity of the additional screen methods.
	"""
	S = module.Screen() # Explicitly utf-8.

	b"-test-title" in test/S.set_window_title_text("-test-title")
	b'!p' in test/S.reset()
	b'2J' in test/S.clear()

	sr = S.set_scrolling_region(0,1)
	b'1' in test/sr
	b'2' in test/sr

	b'7' in test/S.store_cursor_position()
	b'8' in test/S.restore_cursor_position()

	b'9' in test/S.scroll(-9)
	b'10' in test/S.scroll(10)

def test_Context_seek(test):
	"""
	# - &module.Context.seek
	# - &module.Context.tell
	# - &module.Context.seek_last
	"""
	tctx = module.Context()
	tctx.context_set_position((32,32))
	tctx.context_set_dimensions((16, 16))

	b'33' in test/tctx.seek((0,0))
	test/tctx.tell() == (0,0)
	b'48' in test/tctx.seek_last()
	test/tctx.tell() == (15, 15)

def test_Context_properties(test):
	"""
	# - &module.Context
	"""
	ctx = module.Context()

	test.isinstance(ctx.terminal_type, module.Type)
	test/ctx.width == None
	test/ctx.height == None
	test/ctx.point == (None, None)

def test_Context_draw_text(test):
	"""
	# - &module.Context.draw_text
	"""
	ctx = module.Context()

	b'test' in test/ctx.draw_text("test")

def test_Context_subcells_redirect(test):
	"""
	# - &module.Context.subcells

	# Check that redirect display text is sliced directly.
	# Redirects are units too and all word text is included.
	"""

	ctx = module.Context()
	style = ctx.RenderParameters.default
	subcells = ctx.subcells

	u = ctx.Redirect((4, "1234", style, "ABCXYZ"))
	for i in range(1, 4):
		r = subcells(u, 0, i)
		test.isinstance(r, ctx.Redirect)
		test/r[1] == u[1][0:i]
		test/r.text == "ABCXYZ"

	test/subcells(u, 0, 4) == u

def test_Context_subcells_unit(test):
	"""
	# - &module.Context.subcells
	"""

	ctx = module.Context()
	style = ctx.RenderParameters.default
	subcells = ctx.subcells

	u = ctx.Unit((4, "-", style))
	for i in range(1, 4):
		r = subcells(u, 0, i)
		test.isinstance(r, ctx.Redirect)
		test/r[1] == ("+" * i) # Default substitute.
		test/r.text == "-"

	test/subcells(u, 0, 4) == u

def test_Context_subcells_chinese(test):
	"""
	# - &module.Context.subcells
	"""

	ctx = module.Context()
	style = ctx.RenderParameters.default
	subcells = ctx.subcells

	w = ctx.Words((6, "中国人", style))
	r = subcells(w, 1, 6, substitute=":")
	test.isinstance(r, ctx.Redirect)
	test/r[1] == ":" + w[1][1:]
	test/r.text == w[1]

	# First cell of the first codepoint.
	r = subcells(w, 0, 1, substitute=":")
	test.isinstance(r, ctx.Redirect)
	test/r[1] == ":"
	test/r.text == w[1][0]

	# Prefix and suffix.
	r = subcells(w, 1, 3, substitute=":")
	test.isinstance(r, ctx.Redirect)
	test/r[1] == "::"
	test/r.text == w[1][0:2]

	# Prefix and suffix with inner whole.
	r = subcells(w, 1, 5, substitute=":")
	test.isinstance(r, ctx.Redirect)
	test/r[1] == ":" + w[1][1] + ":"
	test/r.text == w[1]

	# Check wholes.
	for i in range(0, 6, 2):
		idx = i // 2
		r = subcells(w, i, i+2, substitute=":")
		test.isinstance(r, ctx.Redirect)
		test/r[1] == w[1][idx:idx+1]
		test/r.text == w[1][idx:idx+1]
