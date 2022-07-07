"""
# Most of the tests here are sanity tests primarily checking to make sure exceptions aren't
# raised from good parameters.
"""
from .. import core
from .. import matrix as module

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
	notraits = core.NoTraits

	leading = (notraits, 0, 0, 0)
	following = (notraits, 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[38;2;0;0;1m'

	# No transition.
	leading = (notraits, 1, 0, 0)
	following = (notraits, 1, 0, 0)
	test/(transition(leading, following)) == b''

	# elimation (underline)
	leading = (core.Traits.construct('underline'), 1, 0, 0)
	following = (notraits, 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[24m'

	# transition in (underline)
	leading = (notraits, 1, 0, 0)
	following = (core.Traits.construct('underline'), 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[4m'

	# transition in underline from double
	leading = (core.Traits.construct('double-underline'), 1, 0, 0)
	following = (core.Traits.construct('underline'), 1, 0, 0)
	test/(transition(leading, following)) == b'\x1b[24;4m'

def test_Type_linecolor_transition(test):
	"""
	# - &module.Type.transition_render_parameters
	# - &module.Type.select_transition
	"""
	t = module.Type('utf-8')
	transition = t.transition_render_parameters

	rp = core.RenderParameters.from_colors(0, 0)
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

def test_Context_render_transitions(test):
	"""
	# - &module.Context.render

	# Validates that &module.Context.transition is properly applied.
	"""
	s = module.Screen()

	# Underline to bold.
	ph = core.Phrase.construct([
		("Simple", s.Traits.construct('underline'), -1024, -1024, -1024),
		(" ", s.Traits.construct('bold'), -1024, -1024, -1024),
		("phrase.", s.Traits.construct('bold'), -1024, -1024, -1024),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'\x1b[24;1m', b' ', b'', b'phrase.']

	# Underline to far bold.
	ph = core.Phrase.construct([
		("Simple", s.Traits.construct('underline'), -1024, -1024, -1024),
		(" ", s.Traits.construct('underline'), -1024, -1024, -1024),
		("phrase.", s.Traits.construct('bold'), -1024, -1024, -1024),
	])
	rph = list(s.render(ph))
	test/rph == [b'\x1b[4m', b'Simple', b'', b' ', b'\x1b[24;1m', b'phrase.']

	# New text.
	ph = core.Phrase.construct([
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
		("Simple", core.Traits(0), -513, -513, -8),
		(" ", core.Traits(0), -513, -513, -8),
		("phrase.", core.Traits(0), -513, -513, -8),
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

	b's' in test/S.store_cursor_location()
	b'u' in test/S.restore_cursor_location()
	b'8' in test/S.scroll_up(8)
	b'8' in test/S.scroll_down(8)

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

def test_Context_draw_words(test):
	"""
	# - &module.Context.draw_words
	"""
	ctx = module.Context()
	b'test' in test/ctx.draw_words("test")

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
