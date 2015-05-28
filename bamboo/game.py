import re
import os.path

import pyglet
from pyglet.window import key
from pyglet import gl

from bamboo.gamestate import GameState, BambooWarriorGameState
from bamboo.menu import MenuGameState

FPS = 30.0

class Game(object):
	def __init__(self, options):
		"""Here options is an optparse object or similar that contains a few
		commandline options for configuring the game, eg. fullscreen and window dims
		"""
		self.init_resources()
		self.window = self.create_window(options)
		self.init_events()
		self.gamestate = GameState()

		if options.showfps:
			self.fps = pyglet.clock.ClockDisplay()
		else:
			self.fps = None

	def init_resources(self):
		pyglet.resource.path = ['resources/sprites', 'resources/textures', 'resources/music', 'resources/sounds', 'resources/levels']
		pyglet.resource.reindex()

	def create_window(self, options):
		mo = re.match(r'(\d+)x(\d+)', options.resolution)
		if mo:
			width = int(mo.group(1))
			height = int(mo.group(2))
		else:
			width = 1280
			height = 720
		
		if options.fullscreen:
			window = pyglet.window.Window(fullscreen=True)
		else:
			window = pyglet.window.Window(width, height)
		window.set_caption('Bamboo Warrior')
		return window

	def on_key_press(self, code, modifiers):
		if code == key.F12:
			print "Wrote", self.save_screenshot()
			return pyglet.event.EVENT_HANDLED
		return self.gamestate.on_key_press(code, modifiers)

	def save_screenshot(self):
		"""Save a screenshot to the grabs/ directory"""
		gl.glPixelTransferf(gl.GL_ALPHA_BIAS, 1.0)	# don't transfer alpha channel
		image = pyglet.image.ColorBufferImage(0, 0, self.window.width, self.window.height)
		n = 1
		outfile = 'grabs/screenshot.png'
		while os.path.exists(outfile):
			n += 1
			outfile = 'grabs/screenshot-%d.png' % n
		image.save(outfile)
		gl.glPixelTransferf(gl.GL_ALPHA_BIAS, 0.0)	# restore alpha channel transfer
		return outfile

	def init_events(self):
		self.keys = key.KeyStateHandler()
		self.window.push_handlers(on_key_press=self.on_key_press, on_draw=self.draw)
		self.window.push_handlers(self.keys)

	def set_gamestate(self, gamestate):
		self.gamestate = gamestate
		gamestate.start()

	def update(self, x):
		"""Update the world, or delegate to something that will"""
		self.gamestate.update(self.keys)

	def draw(self):
		"""Draw the scene, or delegate to something that will"""
		self.gamestate.draw()
		if self.fps:
			self.fps.draw()
	
	def run(self):
		pyglet.clock.schedule_interval(self.update, (1.0/FPS))
		pyglet.clock.set_fps_limit(FPS)
		pyglet.app.run()
