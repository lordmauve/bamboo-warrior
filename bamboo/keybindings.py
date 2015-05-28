import ConfigParser
from pyglet.window import key

class KeyBindingError(ValueError):
	"""The keysym did not exist"""

def _is_pressed(name):
	def is_key_pressed(self, keys):
		for k in getattr(self, name):
			if keys[k]:
				return True
		return False
	return is_key_pressed

class PlayerBindings(object):
	def __init__(self, up, down, left, right, attack, jump):
		self.up = up
		self.down = down
		self.left = left
		self.right = right
		self.attack = attack
		self.jump = jump

	is_jump = _is_pressed('jump')
	is_attack = _is_pressed('attack')
	is_up = _is_pressed('up')
	is_down = _is_pressed('down')
	is_left = _is_pressed('left')
	is_right = _is_pressed('right')


def get_binding(parser, section, name):
	line = parser.get(section, name)
	ks = set()
	for ksym in line.split(','):
		try:
			k = getattr(key, ksym)
		except AttributeError:
			raise KeyBindingError("Unknown key binding symbol '%s': see http://www.pyglet.org/doc/api/pyglet.window.key-module.html for all supported names" % ksym)
		else:
			ks.add(k)
	return ks


def load_bindings():
	p = ConfigParser.SafeConfigParser()
	p.read('keybindings.conf')
	bindings = {
		'player1': PlayerBindings(
			up=[key.UP],
			down=[key.DOWN],
			left=[key.LEFT],
			right=[key.RIGHT],
			attack=[key.RCTRL],
			jump=[key.RSHIFT]
		),

		'player2': PlayerBindings(
			up=[key.W],
			down=[key.S],
			left=[key.A],
			right=[key.D],
			attack=[key.I],
			jump=[key.U]
		)
	}
	for s in p.sections():
		bindings[s] = PlayerBindings(
			up=get_binding(p, s, 'up'),
			down=get_binding(p, s, 'down'),
			left=get_binding(p, s, 'left'),
			right=get_binding(p, s, 'right'),
			jump=get_binding(p, s, 'jump'),
			attack=get_binding(p, s, 'attack')
		)
	return bindings

