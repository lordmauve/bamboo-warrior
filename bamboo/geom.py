import math

ERROR_TOLERANCE = 1e-9

class Vec2(object):
	"""A 2D vector object to make vector maths easy"""
	__slots__ = ('x', 'y', '_mag')

	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __repr__(self):
		return 'Vec2(%r, %r)' % tuple(self)

	def __str__(self):
		return '(%f, %f)' % tuple(self)

	def __add__(self, ano):
		return Vec2(self.x + ano.x, self.y + ano.y)

	def __sub__(self, ano):
		return Vec2(self.x - ano.x, self.y - ano.y)

	def __neg__(self):
		return Vec2(-self.x, -self.y)

	def __mul__(self, scalar):
		return Vec2(self.x * scalar, self.y * scalar)

	def __nonzero__(self):
		return abs(self.x) > ERROR_TOLERANCE or abs(self.y) > ERROR_TOLERANCE

	def __div__(self, scalar):
		return self * (1.0 / scalar)

	__rmul__ = __mul__

	def __iter__(self):
		"""For easy unpacking"""
		yield self.x
		yield self.y

	def mag(self):
		try:
			return self._mag
		except AttributeError:
			self._mag = math.sqrt(self.x * self.x  + self.y * self.y)
			return self._mag
	def mag2(self):
		return self.x * self.x  + self.y * self.y

	def normalized(self):
		# check for mag smaller than a threshold to eliminate a class of numerical error problems
		if not self:
			raise ZeroDivisionError("Normalization of very tiny vector is unlikely to give good results")

		return self / self.mag() 

	def renormalized(self):
		"""Returns a normalized version of this vector.
	
		Differs from .normalized() in that it includes a check whether the vector is already
		normalized. Where a function expects normalized vectors in many but not all cases,
		this may be faster as it skips a sqrt() call in those cases.

		"""
		if abs(self.mag2() - 1) < ERROR_TOLERANCE:
			return self
		return self.normalized()

	def dot(self, ano):
		return self.x * ano.x + self.y * ano.y

	def component_of(self, ano):
		"""Component of ano in the direction of self"""
		return self.dot(ano) * self / self.mag2()

	def rotate(self, angle):
		x = self.x
		y = self.y
		sin = math.sin(angle)
		cos = math.cos(angle)
		return Vec2(cos * x - sin * y, sin * x + cos * y)

	def angle(self):
		return math.atan2(self.y, self.x)

	def rotate_degrees(self, angle):
		return self.rotate(angle * math.pi / 180.0)

	def angle_in_degrees(self):
		return self.angle() / math.pi * 180.0

	def perpendicular(self):
		"""Rotatation through 90 degrees, without trig functions"""
		return Vec2(-self.y, self.x)


class Matrix2(object):
	__slots__ = ('x11', 'x12', 'x21', 'x22')

	def __init__(self, x11, x12, x21, x22):
		self.x11 = x11
		self.x12 = x12
		self.x21 = x21
		self.x22 = x22
	
	def __mul__(self, vec):
		return Vec2(self.x11 * vec.x + self.x12 * vec.y, self.x21 * vec.x + self.x22 * vec.y)

	@staticmethod
	def rotation(angle):
		sin = math.sin(angle)
		cos = math.cos(angle)
		return Matrix2(cos, -sin, sin, cos)
		


class Rect(object):
	"""An axis-aligned rectangle"""
	def __init__(self, l, b, w, h):
		self.l = l
		self.b = b
		self.w = w
		self.h = h

	def _t(self):
		return self.b + self.h
	t = property(_t)

	def _r(self):
		return self.l + self.w
	r = property(_r)

	def bottomleft(self):
		return Vec2(self.l, self.b)

	def topleft(self):
		return Vec2(self.l, self.t)
	
	def topright(self):
		return Vec2(self.r, self.t)

	def bottomright(self):
		return Vec2(self.r, self.b)

	def center(self):
		return Vec2(self.l + self.w * 0.5, self.b + self.h * 0.5)

	def intersects(self, r):
		return r.r > self.l and r.l < self.r \
                	and r.t > self.b and r.b < self.t

	def __nonzero__(self):
		return bool(self.w or self.h)

	def contains(self, point):
		return p.x >= self.l and p.x < self.r \
			and p.y >= self.b and p.y < self.t

	def intersection(self, r):
		if not self.intersects(r):
			return None
		xs = [self.l, self.r, r.l, r.r]
		ys = [self.b, self.t, r.b, r.t]
		xs.sort()
		ys.sort()
		return Rect(xs[1], ys[1], xs[2] - xs[1], ys[2] - ys[1])

	def vertices(self):
		"""Pyglet vertex list"""
		vs = []
		for v in [self.bottomleft(), self.bottomright(), self.topright(), self.topleft()]:
			vs += [v.x, v.y]
		return vs

	def scale_about_center(self, sx, sy=None):
		if sy is None:
			sy = sx
		return Rect.from_center(self.center(), self.w * sx, self.h * sy)

	@staticmethod
	def from_center(c, w, h):
		return Rect(c.x - w * 0.5, c.y - h * 0.5, w, h)

	@staticmethod
	def from_corners(c1, c2):
		x1, x2 = sorted([c1.x, c2.x])
		y1, y2 = sorted([c1.y, c2.y])
		return Rect(x1, y1, x2 - x1, y2 - y1)


class Plane(object):
	"""An 2D line.
	
	The representation of the line allows it to partition space into an
	'outside' and an inside.
	"""

	__slots__ = ('normal', 'distance')

	def __init__(self, v, distance):
		self.normal = v.renormalized()
		self.distance = distance

	def __repr__(self):
		return 'Plane(%r, %r)' % (self.normal, self.distance)

	def altitude(self, p):
		"""Compute the distance from p to the plane; negative
		if p is inside the plane, positive if outside

		>>> Plane(Vec2(0, 1), 1).altitude(Vec2(0, 2))
		1
		>>> Plane(Vec2(1, 0), 2).altitude(Vec2(0, 0))
		-2
		"""
		return self.normal.dot(p) - self.distance

	def is_inside(self, p):
		"""Return True if p is "inside" this plane

		>>> Plane(Vec2(1, 1), 1).is_inside(Vec2(0,0.7))
		True
		>>> Plane(Vec2(-1, 0.5), 2).is_inside(Vec2(-3,0.5))
		False
		"""
		return self.altitude(p) < 0

	def project(self, p):
		return p - self.altitude(p) * self.normal

	def mirror(self, p):
		"""Mirror p in the line of the plane

		>>> m = Plane(Vec2(1, 1), 0).mirror(Vec2(1, 0))
		>>> bool(m - Vec2(0, -1))
		False
		"""
		# TODO: return transformation matrix instead
		return p - 2 * self.altitude(p) * self.normal

	@classmethod
	def from_points(cls, p1, p2):
		n = (p2 - p1).perpendicular()
		d = n.normalized().dot(p1)
		return cls(n, d)


class LineSegment(object):
	"""A line segment defined by start and end points"""
	def __init__(self, p1, p2):
		self.p1 = p1
		self.p2 = p2

	def to_plane(self):
		return Plane.from_points(p1, p2)

	def normal(self):
		"""Return a normalized normal vector"""
		return self.tangent().perpendicular()

	def tangent(self):
		"""Return a tangent vector in the normal direction"""
		return (self.p2 - self.p1).normalized()
		
		

class PolyLine(object):
	"""A set of points connected into line"""

	def __init__(self, vertices=[]):
		self.vertices = vertices

	def __repr__(self):
		return 'PolyLine(%r)' % (self.vertices,)

	def __iter__(self):
		"""Iterate over the vertices"""
		return iter(self.vertices)

	def segments(self):
		nvs = len(self.vertices)
		for i in range(1, nvs):
			yield LineSegment(self.vertices[i - 1], self.vertices[i])


class Polygon(object):
	"""Mutable polygon, possibly with holes, multiple contours, etc.

	This exists mainly as a wrapper for polygon tesselation, but also provides some useful methods"""
	def __init__(self, vertices=None):
		self.contours = []
		if vertices:
			self.add_contour(vertices)

	def mirror(self, plane):
		p = Polygon()
		for c in self.contours:
			mirrored = [plane.mirror(v) for v in reversed(c)]
			p.add_contour(mirrored)
		return p

	def tesselate(self):
		from bamboo.polygontesselator import PolygonTesselator
		return PolygonTesselator().tesselate(self)

	def polylines_facing(self, v, threshold=0):
		"""Compute a list of PolyLines on the edge of this contour whose normals face v.
		
		threshold the value of the segment normal dot v required to include
		a segment in the polyline.
		
		"""
		lines = []
		for contour in self.contours:
			# first work out which segments pass
			segments = []
			nvs = len(contour)
			for i in range(nvs):
				v1 = i
				v2 = (i + 1) % nvs
				segment = LineSegment(contour[v1], contour[v2])
				try:
					normal = segment.normal()
				except ZeroDivisionError:
					continue
				facing = segment.normal().dot(v) > threshold
				segments.append((segment, facing))

			nvs = len(segments)

			# find a non-facing/facing boundary to start
			was_facing = None
			for start in range(nvs):
				facing = segments[start][1]
				if was_facing is None:
					was_facing = facing
				elif was_facing ^ facing:
					break

			# 'start' is now an offset we can start at to find all connected segments
			vs = []
			for i in range(nvs):
				seg, facing = segments[(i + start) % nvs]
				if not facing:
					if vs:
						lines.append(vs)
						vs = []
				else:
					if vs:
						vs.append(seg.p2)
					else:
						vs = [seg.p1, seg.p2]
			if vs:
				lines.append(vs)
		return [PolyLine(vs) for vs in lines if len(vs) >= 2]
		

	def add_contour(self, vertices):
		"""Adds a contour"""
		self.contours.append(vertices)


class ConvexPolygon(object):
	"""A convex polygon is more suitable for mathematical operations than a polygon that is possibly concave."""

	__slots__ = ('vertices',)

	def __init__(self, vertices):
		"""Construct a new ConvexPolygon with the vertex list given.
		
		render_mode is a hint for renderers as to whether to convert this polygon
		to triangles as strips or fans. It is simply stored.

		"""
		self.vertices = tuple(vertices)

	def __repr__(self):
		return 'ConvexPolygon(%r)' % (self.vertices,)

	def __iter__(self):
		"""Iterate over the vertices"""
		return iter(self.vertices)

	def to_tri_strip(self):
		"""Generate a list of the vertices in triangle-strip order"""
		left = 0
		right = len(self.vertices) - 1
		while True:
			yield self.vertices[left]
			yield self.vertices[right]
			
			left += 1
			right -= 1
			if left == right:
				yield self.vertices[left]
			elif left > right:
				break

	def segments(self):
		nvs = len(self.vertices)
		for i in range(nvs):
			v1 = i
			v2 = (i + 1) % nvs
			yield LineSegment(self.vertices[v1], self.vertices[v2])


if __name__ == '__main__':
	import doctest
	doctest.testmod()
