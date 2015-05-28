import sys
import itertools

from ctypes import CFUNCTYPE, POINTER, byref, cast, pointer
from pyglet.gl import *

from bamboo.geom import Vec2, ConvexPolygon

"""Polygon Tesselator.

Portions copyright (c) 2008 Martin O'Leary.
Adapted by Daniel Pope 2010.

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met: 

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.
* Neither the name(s) of the copyright holders nor the names of its contributors
  may be used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.

"""

# modified from squirtle - licensed under a BSD license
# see http://www.supereffective.org/pages/Squirtle-SVG-Library


if sys.platform == 'win32':
    from ctypes import WINFUNCTYPE
    c_functype = WINFUNCTYPE
else:
    c_functype = CFUNCTYPE
    
callback_types = {GLU_TESS_VERTEX: c_functype(None, POINTER(GLvoid)),
                  GLU_TESS_BEGIN: c_functype(None, GLenum),
                  GLU_TESS_END: c_functype(None),
                  GLU_TESS_ERROR: c_functype(None, GLenum),
                  GLU_TESS_COMBINE: c_functype(None, POINTER(GLdouble), POINTER(POINTER(GLvoid)), POINTER(GLfloat), POINTER(POINTER(GLvoid)))}


def set_tess_callback(tess, which, func):
	"""Set a Python callable as a gluTessCallback.

	Slightly modified from Squirtle implementatation which acts as a decorator.

	"""
        cb = callback_types[which](func)
        gluTessCallback(tess, which, cast(cb, CFUNCTYPE(None)))
        return cb


class PolygonTesselationError(Exception):
	"""Python wrapper for a GLU tesselation error"""


class TriangleStrip(object):
	def __init__(self, vertices):
		self.vertices = vertices

	def triangles(self):
		vs = self.vertices[:]
		p1 = vs.pop(0)
		p2 = vs.pop(0)
		while vs: 
			p3 = vs.pop(0)
			yield ConvexPolygon([p1, p2, p3])
			p1 = p2
			p2 = p3

	def gl_vertices(self):
		return GL_TRIANGLE_STRIP, self.vertices


class TriangleFan(object):
	def __init__(self, vertices):
		self.vertices = vertices

	def triangles(self):
		vs = self.vertices[:]
		c = vs.pop(0)
		p2 = vs.pop(0)
		while vs:
			p3 = vs.pop(0)
			yield ConvexPolygon([c, p2, p3])
			p2 = p3

	def gl_vertices(self):
		vs = []
		for t in self.triangles():
			vs += reversed(t.vertices)
		return GL_TRIANGLES, vs


class TriangleList(object):
	def __init__(self, vertices):
		self.vertices = vertices

	def triangles(self):
		vs = self.vertices[:]
		while vs:
			yield ConvexPolygon(vs[:3])
			vs = vs[3:]
	
	def gl_vertices(self):
		return GL_TRIANGLES, self.vertices


class PolygonTesselator(object):
	"""Splits Polygons into a list of ConvexPolygons.

	The current implementation (using gluTess* functions) merely splits an abstract
	geometric polygon; the relationship between the original polygon and the split
	polygons is not recorded. Such a thing is possible using GLU.

	GLU also provides type information: whether to draw with strips or fans. A convex
	polygon can be drawn with either, but GLU may be providing useful hints as to
	which to use for best results (it affects values that are interpolated along
	triangle edges, such as vertex colour).

	"""
	WINDING_ODD = GLU_TESS_WINDING_ODD
	WINDING_NONZERO = GLU_TESS_WINDING_NONZERO
	WINDING_POSITIVE = GLU_TESS_WINDING_POSITIVE
	WINDING_NEGATIVE = GLU_TESS_WINDING_NEGATIVE
	WINDING_ABS_GEQ_TWO = GLU_TESS_WINDING_ABS_GEQ_TWO

	def __init__(self, winding_rule=WINDING_ODD):
		tess = gluNewTess() # is this expensive?
		gluTessNormal(tess, 0, 0, 1)
		gluTessProperty(tess, GLU_TESS_WINDING_RULE, winding_rule)
		callbacks = [] 
		callbacks.append(set_tess_callback(tess, GLU_TESS_BEGIN, self.tess_begin))
		callbacks.append(set_tess_callback(tess, GLU_TESS_VERTEX, self.tess_vertex))
		callbacks.append(set_tess_callback(tess, GLU_TESS_END, self.tess_end))
		callbacks.append(set_tess_callback(tess, GLU_TESS_COMBINE, self.tess_combine))
		callbacks.append(set_tess_callback(tess, GLU_TESS_ERROR, self.tess_error))
		self.callbacks = callbacks	# hold references to callbacks to avoid them being garbage collected
		self.tess = tess

	def tess_begin(self, type):
		self.type = type
		self.vertices = []

	def tess_vertex(self, v):
		"""Add a Gldouble[3] vertex to the current poly as a Vec2"""
		vertex = cast(v, POINTER(GLdouble))
		vert = Vec2(float(vertex[0]), float(vertex[1]))
		self.vertices.append(vert)

	def tess_end(self):
		if self.type == GL_TRIANGLE_FAN:
			self.batches.append(TriangleFan(self.vertices))
		elif self.type == GL_TRIANGLE_STRIP:
			self.batches.append(TriangleStrip(self.vertices))
		elif self.type == GL_TRIANGLES:
			self.batches.append(TriangleList(self.vertices))
		else:
			raise PolygonTesselationError("Unsupported GL primitive %d in tesselation" % self.type)
		self.vertices = []

	def tess_combine(self, coords, vertex_data, weight, outdata):
		x, y, z = coords[0:3]
		data = (GLdouble * 3)(x, y, z)
		outdata[0] = cast(pointer(data), POINTER(GLvoid))
		self.spareverts.append(data)

	def tess_error(self, code):
		ptr = gluErrorString(code)
		err = ''
		idx = 0
		while ptr[idx]: 
			err += chr(ptr[idx])
			idx += 1
		raise PolygonTesselationError(gluErrorString(err)) 

	def tesselate(self, polygon):
		"""Return a list of ConvexPolygons for the given polygon."""
		self.batches = []
		self.spareverts = []

		# Pack vertices into an array
		# The tesselator maintains pointers into this data, so this must
		# not change while the tesselator is running		
		data = [[(GLdouble * 3)(x, y, 0) for x, y in c] for c in polygon.contours]

		gluTessBeginPolygon(self.tess, None)
		for contour in data:
			gluTessBeginContour(self.tess)
			for vertex in contour:
				gluTessVertex(self.tess, vertex, vertex)
			gluTessEndContour(self.tess)
		gluTessEndPolygon(self.tess)
		return self.batches

	def __del__(self):
		gluDeleteTess(self.tess)
