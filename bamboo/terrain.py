import itertools
from bamboo.geom import Vec2


class Terrain(object):
	def __init__(self, polygon):
		"""Create the terrain from a polygon"""
		self.polygon = polygon
		self.render_groups = self.polygon.tesselate()

	def get_render_groups(self):
		return self.render_groups

	def get_collision_shapes(self):
		return itertools.chain.from_iterable(g.triangles() for g in self.render_groups)

	def height_at(self, x):
		return 60

	def normal_at(self, x):
		return Vec2(0, 1)

	def update(self):
		pass
