import pyglet
from pyglet.gl import *
from pyglet.window import key

from bamboo.resources import ResourceTracker
from bamboo.gamestate import GameState, StaticLevelGameState


class MenuItem(object):
	def __init__(self, label, callback):
		self.label = label
		self.callback = callback

	def update_batch(self, batch, x, y):
		self.l = pyglet.text.Label(self.label, font_name='URW Gothic L', font_size=19, x=x, y=y, color=(0,0,0,255), batch=batch, anchor_x='center')

	def r(self):
		return self.l.x + self.l.content_width // 2, self.l.y

	def action(self):
		self.callback()


class Menu(ResourceTracker):
	def __init__(self, game):
		self.game = game
		self.options = []
		self.message = None
		self.setup_options()
		self.batch = None
		self.selected_option = 0

	def setup_options(self):
		pass

	def add_option(self, label, callback):
		self.options.append(MenuItem(label, callback))

	def set_message(self, message):
		self.message = message

	@classmethod
	def on_class_load(cls):
		cls.load_texture('menubg', 'menubg.png')
		cls.load_sprite('logo', 'logo.png')
		cls.load_sprite('sel', 'menu-selection.png', anchor_x=-8, anchor_y=-8)

	def create_batch(self, window):
		batch = pyglet.graphics.Batch()

		bg = self.textures['menubg']
		r = int(window.width * 0.95) + 30
		l = r - bg.width
		c = r - bg.width //2

		th = float(window.height)/float(bg.height)
		group = pyglet.sprite.SpriteGroup(bg, gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, parent=pyglet.graphics.OrderedGroup(1))
		self.bg = batch.add(4, GL_QUADS, group,
			('v2i', [l,0, r,0, r,window.height, l,window.height]),
			('t2f', [bg.tex_coords[0],0, bg.tex_coords[3],0, bg.tex_coords[3],th, bg.tex_coords[0],th])
		)

		self.logo = pyglet.sprite.Sprite(self.graphics['logo'], batch=batch, group=pyglet.graphics.OrderedGroup(2), x=c, y=window.height - 200)
		self.batch = batch

		y = window.height - 300

		if self.message:
			col = (0x6c, 0x88, 0x4b, 0xff)
			self.message_label = pyglet.text.Label(self.message, font_name='URW Gothic L', font_size=19, x=c, y=y, color=col, batch=batch, anchor_x='center')
			y -= 100

		for i, o in enumerate(self.options):
			o.update_batch(batch, c, y)

			if i == self.selected_option:
				self.sel = pyglet.sprite.Sprite(self.graphics['sel'], batch=batch, group=pyglet.graphics.OrderedGroup(2), x=o.r()[0], y=y)

			y -= 50

	def get_selected_option(self):
		return self.options[self.selected_option]

	def next_option(self):
		self.selected_option = (self.selected_option + 1) % len(self.options)
		self.sel.position = self.get_selected_option().r()

	def prev_option(self):
		self.selected_option = (self.selected_option - 1) % len(self.options)
		self.sel.position = self.get_selected_option().r()

	def select_option(self):
		self.get_selected_option().action()

	def draw(self):
		self.batch.draw()
		


class MenuGameState(GameState):
	def __init__(self, game, menu=None, child=None):
		self.game = game
		if child is None:
			child = StaticLevelGameState(game)
		self.child = child
		if menu is None:
			menu = MainMenu(game)
		self.set_menu(menu)

	def start(self):
		pass

	def set_menu(self, menu):
		menu.load_resources()
		menu.create_batch(self.game.window)	
		self.menu = menu

	def update(self, keys):
		pass

	def on_key_press(self, code, modifiers):
		if code == key.UP:
			self.menu.prev_option() 
		elif code == key.DOWN:
			self.menu.next_option() 
		elif code == key.ENTER:
			self.menu.select_option()

	def draw(self):
		if self.child:
			self.child.draw()
		self.menu.draw()	


class MainMenu(Menu):
	def setup_options(self):
		self.add_option('start new game', self.start_new_game)
		self.add_option('multiplayer game', self.start_multiplayer_game)
		self.add_option('exit game', self.exit_game)

	def start_new_game(self):
		from bamboo.gamestate import BambooWarriorGameState
		self.game.set_gamestate(BambooWarriorGameState(self.game))

	def start_multiplayer_game(self):
		from bamboo.gamestate import MultiplayerGameState
		self.game.set_gamestate(MultiplayerGameState(self.game))

	def exit_game(self):
		pyglet.app.exit()


class InGameMenu(Menu):
	def setup_options(self):
		self.add_option('continue game', self.continue_game)
		self.add_option('restart level', self.restart_level)
		self.add_option('main menu', self.main_menu)
		self.add_option('exit game', self.exit_game)

	def continue_game(self):
		self.game.gamestate = self.game.gamestate.child

	def main_menu(self):
		self.game.set_gamestate(MenuGameState(self.game, MainMenu(self.game)))

	def restart_level(self):
		self.continue_game()
		self.game.gamestate.restart_level()

	def exit_game(self):
		pyglet.app.exit()


class GameOverMenu(InGameMenu):
	def setup_options(self):
		self.set_message('game over')
		self.add_option('restart level', self.restart_level)
		self.add_option('main menu', self.main_menu)
		self.add_option('exit game', self.exit_game)


class EndGameMenu(InGameMenu):
	def setup_options(self):
		self.set_message('you win')
		self.add_option('main menu', self.main_menu)
		self.add_option('exit game', self.exit_game)
