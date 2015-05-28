import math
import random

import pyglet
from pyglet.gl import *

from base import Actor

from bamboo.geom import Vec2, Matrix2, Rect


class Climbable(object):
	def __init__(self):
		self.actors = []

	def is_climbable(self):
		return True

	def add_actor(self, a):
		a.climbing = self
		try:
			a.climbing_height = self.height_for_y(a.pos.y)
		except ValueError:
			a.climbing_height = self.height - 2
		self.actors.append(a)

	def remove_actor(self, a):
		a.climbing = None
		a.climb_rate = None
		self.actors.remove(a)

	def climb_up(self, a, dist=10.0):
		a.climbing_height = min(self.height - 2, a.climbing_height + float(dist) / self.PIECE_HEIGHT)

	def climb_down(self, a, dist=10.0):
		a.climbing_height = max(0, a.climbing_height - float(dist) / self.PIECE_HEIGHT)
		if a.climbing_height == 0:
			self.remove_actor(a)

	def height_for_y(self, y):
		raise NotImplementedError("Climbable objects must implement .height_for_y()")

	def distance_from(self, pos):
		raise NotImplementedError("Climbable objects must implement .distance_from()")


class BambooTree(Actor, Climbable):
	PIECE_HEIGHT = 96
	RADIUS = 12.5
	TEX_PERIOD = 1.5
	THINNING = 0.96 ** TEX_PERIOD		# trees get thinner as you go up, by this ratio per segment

	def __init__(self, x=60, height=9, angle=0):
		Climbable.__init__(self)
		self.height = height
		self.pos = Vec2(x, 0)
		self.base_angle = angle
		self.wobble_angle = 0
		self.wind_phase = 0
		self.batch = None

	def on_spawn(self):
		self.wind_phase = 0.1 * self.pos.x

	def distance_from(self, p):
		"""Estimate the distance from x, y to this tree. This only works for small wobbly angles."""
		da = self.wobble_angle / self.height

		rotation = Matrix2.rotation(da)
		pos = self.pos
		step = Vec2(0, self.PIECE_HEIGHT).rotate(self.base_angle)
		radius = Vec2(self.RADIUS, 0).rotate(self.base_angle)

		if pos.y > p.y:
			return (p - pos).mag()

		for i in range(self.height + 1):
			if pos.y > p.y:
				return abs(pos.x - p.x)
			pos += step
			step = rotation * step
		
		return (p - pos).mag()

	def height_for_y(self, y):
		"""Estimate the height in this tree for a coordinate of y. This only works for small wobble angles."""
		da = self.wobble_angle / self.height

		rotation = Matrix2.rotation(da)
		pos = self.pos
		step = Vec2(0, self.PIECE_HEIGHT).rotate(self.base_angle)
		radius = Vec2(self.RADIUS, 0).rotate(self.base_angle)

		for i in range(self.height + 1):
			if step.y <= 0:
				raise ValueError("Tree does not reach a height of %f." % y)
			next = pos + step
			if next.y >= y:
				return i + float(y - pos.y) / step.y
			pos += step
			step = rotation * step
		raise ValueError("Tree does not reach a height of %f." % y)

	@classmethod
	def on_class_load(cls):
		cls.load_texture('piece', 'bamboo-piece.png', anchor_x='center')
		cls.load_directional_sprite('leaf1', 'bamboo-leaf1.png', anchor_x='right')
		cls.load_directional_sprite('leaf2', 'bamboo-leaf2.png', anchor_x='right')
		cls.load_sprite('top', 'bamboo-top.png', anchor_x=77, anchor_y=3)

	def get_parent_group(self, parent=None):
		return parent

	def update_batch(self, batch, parent=None):
		if self.batch:
			self.update_vertexlist()
		else:
			self.init_batch(batch, parent)
			self.batch = batch

	def init_batch(self, batch, parent):
		tex = self.textures['piece']
		vertices = []
		tex_coords = []

		da = self.wobble_angle / self.height
		pos = self.pos
		step = Vec2(0, self.PIECE_HEIGHT).rotate(self.base_angle)
		radius = Vec2(self.RADIUS, 0).rotate(self.base_angle)

		for v in self.tree_vertices():
			vertices += [v.x, v.y]

		for i in range(self.height + 1):
			tex_coords += [tex.tex_coords[0], (i + 1) * self.TEX_PERIOD, tex.tex_coords[3], (i + 1) * self.TEX_PERIOD]

		vertices = vertices[:2] + vertices + vertices[-2:]
		tex_coords = tex_coords[:2] + tex_coords + tex_coords[-2:]

		parent_group = self.get_parent_group(parent)
		group = pyglet.sprite.SpriteGroup(self.textures['piece'], GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, parent=parent_group)
		self.vertex_list = batch.add((self.height + 2) * 2, GL_QUAD_STRIP, group, ('v2f/stream', vertices), ('t2f/static', tex_coords))
	
		self.foliage = []
		for i in range(self.height):
			prob = self.height - i
			if random.random() * prob < 1:
				l = random.choice(['leaf1-l', 'leaf2-l'])
				right = pyglet.sprite.Sprite(self.graphics[l], x=self.pos.x, y=self.PIECE_HEIGHT * i + self.pos.y, batch=batch, group=parent_group)
			else:
				right = None
			if random.random() * prob < 1:
				l = random.choice(['leaf1-r', 'leaf2-r'])
				left = pyglet.sprite.Sprite(self.graphics[l], x=self.pos.x, y=self.PIECE_HEIGHT * i + self.pos.y, batch=batch, group=parent_group)
			else:
				left = None
			self.foliage.append((left, None, right))
		top = pyglet.sprite.Sprite(self.graphics['top'], batch=batch, group=parent_group)
		self.foliage.append((None, top, None))

	def update_vertexlist(self):
#		for i, v in enumerate(self.compute_wobble()):
#			if i == 0:
#				self.set_trunk_vertex(0, v)
#			elif i == self.height * 2 + 1:
#				self.set_trunk_vertex(self.height * 2 + 3, v)
#			self.set_trunk_vertex(i + 1, v)

		vertices = []
		for v in self.compute_wobble():
			vertices += [v.x, v.y]

		self.vertex_list.vertices = vertices[:2] + vertices + vertices[-2:]

	def set_trunk_vertex(self, i, v):
		x, y = v
		self.vertex_list.vertices[i * 2] = x
		self.vertex_list.vertices[i * 2 + 1] = y

	def tree_vertices(self):
		da = self.wobble_angle / self.height

		pos = self.pos
		rotation = Matrix2.rotation(da)
		step = Vec2(0, self.PIECE_HEIGHT)
		radius = Vec2(self.RADIUS, 0)
		angle = 0

		actor_segments = {}
		for a in self.actors:
			h = int(a.climbing_height)
			actor_segments.setdefault(h, []).append(a)

		vertices = []
		for i in range(self.height + 1):
			vertices.append(pos - radius)
			vertices.append(pos + radius)

			pos += step
			step = rotation * step
			angle = angle + da
			radius = (rotation * radius) * self.THINNING
		return vertices

	def compute_wobble(self):
		"""Generator for the vertex list. Iterate to give a sequence of Vec2 objects"""
		da = self.wobble_angle / self.height

		pos = self.pos
		rotation = Matrix2.rotation(da)
		step = Vec2(0, self.PIECE_HEIGHT)
		radius = Vec2(self.RADIUS, 0)
		angle = 0

		steprotation = -da * 180 / math.pi

		actor_segments = {}
		for a in self.actors:
			h = int(a.climbing_height)
			actor_segments.setdefault(h, []).append(a)

		vertices = []
		for i in range(self.height + 1):
			vertices.append(pos - radius)
			vertices.append(pos + radius)
			for side, f in enumerate(self.foliage[i]):
				if f is None:
					continue
				p = pos + (side - 1) * radius
				f.x = p.x
				f.y = p.y
				f.rotation = angle

			for a in actor_segments.get(i, []):
				h = a.climbing_height - i
				apos = pos + h * step
				a.v = apos - a.pos
				a.pos = apos
				a.rotation = angle

			pos += step
			step = rotation * step
			angle += steprotation
			radius = (rotation * radius) * self.THINNING
		return vertices

	def update(self):
		self.wind_phase += 1.0 / self.height
		self.wobble_angle = 0.4 * math.sin(self.wind_phase) + 0.2 * math.sin(self.wind_phase * 0.21) 
		#self.compute_wobble()

	def cull_bounds(self):
		return Rect(self.pos.x - 250, self.pos.y, 500, self.height * self.PIECE_HEIGHT + 200)

	def draw(self):
		self.batch.draw()



class BackgroundGroup(pyglet.graphics.Group):
	def __init__(self, depth=0.5, parent=None):
		super(BackgroundGroup, self).__init__(parent)
		self.depth = depth
	
	def set_state(self):
		d = self.depth
		glColor3f(d, d, d)

	def unset_state(self):
		glColor3f(1, 1, 1)

	def __eq__(self, ano):
		return self.__class__ == ano.__class__ and self.depth == ano.depth
		

class BackgroundBambooTree(BambooTree):
	RADIUS = 8
	
	PIECE_HEIGHT = 128
	TEX_PERIOD = 2

	def __init__(self, *args, **kwargs):
		self.shadow = random.random() * 0.7
		super(BackgroundBambooTree, self).__init__(*args, **kwargs)	

	def is_climbable(self):
		return False

	@classmethod
	def on_class_load(cls):
		cls.load_texture('piece', 'bamboo-piece-blurred.png', anchor_x='center')

	def on_spawn(self):
		self.RADIUS = random.random() ** 0.5 * 10 + 2
		self.wobble_angle = random.random() * 1 - 0.5
		self.compute_wobble()

	def get_parent_group(self, parent=None):
		return BackgroundGroup(self.shadow, parent=parent)

	def update(self):
		pass
