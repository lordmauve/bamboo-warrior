import math

import pyglet
from pyglet.gl import *

from bamboo.geom import Vec2
from bamboo.resources import ResourceTracker
from bamboo.renderers import pad_coord_list


class TerrainGroup(pyglet.graphics.Group):
	def __init__(self, colour, texture, colour_scale=1/1024.0, texture_scale=1/256.0, parent=None):
		super(TerrainGroup, self).__init__(parent)
		self.colour = colour
		self.colour_scale = colour_scale
		self.texture = texture
		self.texture_scale = texture_scale

	def enable_texgen(self, scale):
		"""Enable GL generation of texture coordinates"""
		glEnable(GL_TEXTURE_GEN_S)
		glEnable(GL_TEXTURE_GEN_T)
		glTexGenf(GL_S, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
		glTexGenfv(GL_S, GL_OBJECT_PLANE, (GLfloat * 4)(scale, 0, 0, 0))
		glTexGenf(GL_T, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
		glTexGenfv(GL_T, GL_OBJECT_PLANE, (GLfloat * 4)(0, scale, 0, 0))

	def set_state(self):
		glActiveTexture(GL_TEXTURE0)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.colour.id)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

		self.enable_texgen(self.colour_scale)

		glActiveTexture(GL_TEXTURE1)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texture.id)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

		self.enable_texgen(self.texture_scale)
	
		glActiveTexture(GL_TEXTURE0)

	def unset_state(self):
		glActiveTexture(GL_TEXTURE1)
		glDisable(GL_TEXTURE_GEN_S)
		glDisable(GL_TEXTURE_GEN_T)
		glDisable(GL_TEXTURE_2D)
		glActiveTexture(GL_TEXTURE0)
		glDisable(GL_TEXTURE_GEN_S)
		glDisable(GL_TEXTURE_GEN_T)


class GrassStrip(ResourceTracker):
	"""A strip of grass"""
	def __init__(self, polyline):
		self.polyline = polyline

	@classmethod
	def on_class_load(cls):
		cls.load_texture('grass', 'grass.png')

	def create_batch(self, batch, parent=None):
		self.load_resources()
		grassgroup = pyglet.sprite.SpriteGroup(self.textures['grass'], GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, parent=parent)

		grass_vertices = []
		grass_texcoords = []

		grass = self.textures['grass']

		for v in self.polyline:
			# TODO: split grass at regular intervals for wind effect
			grass_vertices += [v.x, v.y - 5, v.x, v.y + grass.height - 5]
			grass_texcoords += [v.x / 128.0, grass.tex_coords[1], v.x / 128.0, grass.tex_coords[7]]

		grass_vertices = pad_coord_list(grass_vertices, 2)
		grass_texcoords = pad_coord_list(grass_texcoords, 2)

		self.list = batch.add(len(grass_vertices) / 2, GL_TRIANGLE_STRIP, grassgroup, ('v2f/stream', grass_vertices), ('t2f/static', grass_texcoords))

	def update(self, wind_phase):
		"""Update the sway of the grass"""
		for i, v in enumerate(self.polyline):
			dx = 4 * math.sin(wind_phase + v.x / 128.0 * 0.5) + 3 * math.sin(wind_phase * 0.375 + v.x / 128.0 * 0.5)
			self.grass_list.vertices[i * 4] = v.x + dx * -0.2
			self.grass_list.vertices[i * 4 + 2] = v.x + dx


class TerrainRenderer(ResourceTracker):
	def __init__(self, terrain):
		self.terrain = terrain
		self.wind_phase = 0
		self.grow_grass()

	def grow_grass(self):
		# find polylines where all segments face the up vector
		polylines = self.terrain.polygon.polylines_facing(Vec2(0, -1), 0.3)
		self.grass_strips = [GrassStrip(pl) for pl in polylines]

	@classmethod
	def on_class_load(cls):
		cls.load_texture('earth', 'earth.png')
		cls.load_texture('earth-colour', 'earth-colour.png')

	def create_batch(self):
		self.load_resources()
		layer1 = pyglet.graphics.OrderedGroup(1)
		layer2 = pyglet.graphics.OrderedGroup(2)
		earthgroup = TerrainGroup(self.textures['earth-colour'], self.textures['earth'], parent=layer1)
		
		batch = pyglet.graphics.Batch()

		for group in self.terrain.get_render_groups():
			earth_vertices = []

			mode, vertices = group.gl_vertices()
			for v in vertices:
				earth_vertices += [v.x, v.y]

			if not earth_vertices:
				continue

			if mode == GL_TRIANGLE_STRIP:
				earth_vertices = pad_coord_list(earth_vertices)
			
			batch.add(len(earth_vertices) / 2, mode, earthgroup, ('v2f/static', earth_vertices))

		for strip in self.grass_strips:
			strip.create_batch(batch, layer2)
		
		self.batch = batch

	def update(self):
		"""Update the grass animation"""
		self.wind_phase += 0.08

	def draw(self):
		self.batch.draw()


class WireframeTerrainRenderer(TerrainRenderer):
	def create_batch(self):
		layer1 = pyglet.graphics.OrderedGroup(1)
		
		batch = pyglet.graphics.Batch()

		for contour in self.terrain.polygon.contours:
			earth_vertices = []

			for v in contour:
				earth_vertices += [v.x, v.y]

			earth_vertices = pad_coord_list(earth_vertices)
			batch.add(len(earth_vertices) / 2, GL_LINE_STRIP, layer1, ('v2f/static', earth_vertices))
		
		self.batch = batch

class WireframePolyTerrainRenderer(TerrainRenderer):
	def create_batch(self):
		layer1 = pyglet.graphics.OrderedGroup(1)
		
		batch = pyglet.graphics.Batch()

		for poly in self.terrain.get_convex_polygons():
			earth_vertices = []

			for v in poly:
				earth_vertices += [v.x, v.y]
			earth_vertices += earth_vertices[:2]

			earth_vertices = pad_coord_list(earth_vertices)
			batch.add(len(earth_vertices) / 2, GL_LINE_STRIP, layer1, ('v2f/static', earth_vertices))
		
		self.batch = batch
