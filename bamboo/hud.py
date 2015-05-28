import pyglet
from pyglet.gl import *

from bamboo.geom import Rect
from bamboo.resources import ResourceTracker


class HUD(ResourceTracker):
	def __init__(self, window, player, side='l', col=(255, 255, 255)):
		self.window = window
		self.player = player
		self.side = side
		self.col = col
		self.batch = None

	def get_frac_health(self):
		if self.player.health < 0:
			return 0.0
		return self.player.health / float(self.player.MAX_HEALTH)

	def get_lives(self):
		try:
			return self.player.lives
		except AttributeError:
			return 0

	@classmethod
	def on_class_load(cls):
		cls.load_sprite('player-icon', 'player-icon.png', anchor_x=0, anchor_y='top')
		cls.load_sprite('life-icon', 'life-icon.png', anchor_y='top')
		cls.load_sprite('bar-full', 'healthbar-full.png', anchor_x=0, anchor_y='top')
		cls.load_sprite('bar-empty', 'healthbar-empty.png', anchor_x=0, anchor_y='top')

	def create_batch(self):
		y = self.window.height - 10
		self.batch = pyglet.graphics.Batch()
		self.icon = pyglet.sprite.Sprite(self.graphics['player-icon'], x=5, y=y + 5, batch=self.batch)
		self.icon.color = self.col
		self.bar_empty = pyglet.sprite.Sprite(self.graphics['bar-empty'], x=74, y=y, batch=self.batch)

		self.life_icons = []
		for i in range(self.get_lives()):
			self.life_icons.append(pyglet.sprite.Sprite(self.graphics['life-icon'], x=64 + 30 + 256 + 8 * i, y=y + 3, batch=self.batch))

		frac = self.get_frac_health()
		w = int(frac * 256 + 0.5)
		r = Rect(74, y - 25, w, 25)
		tex = self.graphics['bar-full']
		group = pyglet.sprite.SpriteGroup(tex, gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
		coords = list(tex.tex_coords[:])
		coords[3] = frac * coords[3] + (1.0 - frac) * coords[0]
		coords[6] = frac * coords[3] + (1.0 - frac) * coords[0]
		self.health_bar = self.batch.add(4, GL_QUADS, group,
			('v2i', r.vertices()),
			('t3f', coords)
		)
		

	def update_batch(self):
		if not self.batch:
			self.create_batch()
		else:
			frac = self.get_frac_health()
			w = int(frac * 256 + 0.5) + 74
			vs = self.health_bar.vertices
			vs[2] = w
			vs[4] = w
			texcoords = list(self.graphics['bar-full'].tex_coords[:])
			coords = self.health_bar.tex_coords
			coords[3] = frac * texcoords[3] + (1.0 - frac) * texcoords[0]
			coords[6] = frac * texcoords[3] + (1.0 - frac) * texcoords[0]

			lives = self.get_lives()
			for i, s in enumerate(self.life_icons[:]):
				if i >= lives:
					s.delete()
					self.life_icons.remove(s)

	def draw(self):
		if self.side == 'r':
			glPushMatrix()
			glTranslatef(self.window.width, 0, 0)
			glScalef(-1,1,1)
			self.batch.draw()
			glPopMatrix()
		else:
			self.batch.draw()
