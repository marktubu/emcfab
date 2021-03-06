"""
	Python wrappers for various OCC primatives.
	These objects make dealing with OCC primatives easier, but also
	a bit slower.
 
"""
#pure python imports
import time,os,sys,string;
import itertools

# OCC imports
from OCC import BRep,gp,GeomAbs,GeomAPI,GCPnts,TopoDS,BRepTools,GeomAdaptor,TopAbs,TopTools,TopExp,Approx,BRepLib,Bnd,BRepBndLib
from OCC import BRepGProp,BRepLProp, BRepBuilderAPI,BRepPrimAPI,GeomAdaptor,GeomAbs,BRepClass,GCPnts,BRepBuilderAPI,BRepOffsetAPI,BRepAdaptor
from OCC import ShapeFix,ShapeExtend,GProp,CPnts

#project imports
from Constants import *;
import OCCUtil

brepTool = BRep.BRep_Tool();
topoDS = TopoDS.TopoDS();

def tP(pnt):
	return (pnt.X(),pnt.Y());

"""
	Wraps a point.. helpful for debugging
"""
class Pnt:
	def __init__(self,p):
		self.pnt = p;
		self.X = p.X();
		self.Y = p.Y();
		self.Z = p.Z();

	def __str__(self):
		return "[Point: ( %0.3f,%0.3f,%0.3f )]" % ( self.X, self.Y, self.Z );
class Vec:
	def __init__(self,v):
		self.vec = v;
		self.X = v.X();
		self.Y = v.Y();
		self.Z = v.Z();

	def __str__(self):
		return "[Vector: ( %0.3f,%0.3f,%0.3f )]" % ( self.X, self.Y, self.Z );
	
	
"""
	Class that provides easy access to commonly
	needed features of a solid shape
"""
class Solid:
	def __init__(self,shape):
		self.shape = shape;

		box = Bnd.Bnd_Box();
		b = BRepBndLib.BRepBndLib();
		b.Add(shape,box);
		
		self.bounds = box.Get();
		self.xMin = self.bounds[0];
		self.xMax = self.bounds[3];
		self.xDim = abs(self.xMax - self.xMin);
		self.yMin = self.bounds[1];
		self.yMax = self.bounds[4];
		self.yDim = abs(self.yMax - self.yMin);
		self.zMin = self.bounds[2];
		self.zMax = self.bounds[5];
		self.zDim = abs(self.zMax - self.zMin);
		
	"""
		Pretty print dimensions
	"""		
	def friendlyDimensions(self):		
		formatString = "x:%0.2f y:%0.2f z:%0.2f (" + self.guessUnitOfMeasure() + ")" 
		return formatString % ( self.xDim, self.yDim, self.zDim );
	
		
	"""
		Translate the shape such that the bottom is at z=0, and the center is at the specified x,y location		
		x : center of the object on x
		y : center of the object on y
	"""	
	def translateToPositiveCenter(self,xCenter,yCenter):

			xT = xCenter - self.xMin  + ( self.xDim / 2.0 );
			yT = yCenter - self.yMin  + ( self.yDim / 2.0 );
			zT = self.zMin*(-1.0);			
			xCenter = abs(self.xMin);
			y = abs(self.yMin);
			z = abs(self.zMin);
			p1 = gp.gp_Pnt(0,0,0);
			p2 = gp.gp_Pnt(xT,yT,zT);
			xform = gp.gp_Trsf();
			xform.SetTranslation(p1,p2);
			bt = BRepBuilderAPI.BRepBuilderAPI_Transform(xform);
			bt.Perform(self.shape,False);
			return Solid(bt.Shape());
	
	"""
	  Given a list of dimenions, guess the unit of measure.
	  The idea is that usually, the dimenions are either in or mm, and its normally evident which one it is
	"""
	def guessUnitOfMeasure(self):
	
		dimList = [ abs(self.xMax - self.xMin ), abs(self.yMax - self.yMin ), abs(self.zMax - self.zMin) ];
		#no real part would likely be bigger than 10 inches on any side
		if max(dimList) > 10:
			return UNITS_MM;
	
		#no real part would likely be smaller than 0.1 mm on all dimensions
		if min(dimList) < 0.1:
			return UNITS_IN;
			
		#no real part would have the sum of its dimensions less than about 5mm
		if sum(dimList) < 10:
			return UNITS_IN;
		
		return UNITS_MM;	

	"""
		fixes problems with a shape-- usually for STL
	"""
	def fixDefects(self):
		"""
			fixes a shape
		"""
		sf = ShapeFix.ShapeFix_Shape(self.shape);
		sf.SetMaxTolerance(TOLERANCE);
	
		msgRegistrator = ShapeExtend.ShapeExtend_MsgRegistrator();
		sf.SetMsgRegistrator(msgRegistrator.GetHandle() );
		
		sf.Perform();
		
		#log.info("ShapeFix Complete.");
		#for i in range(0,18):
		#	log.info( "ShapeFix Status %d --> %s" % ( i, sf.Status(i) ));
			
		fixedShape = sf.Shape();
		#fixedShape = shape;
		
		#if the resulting shape is a compound, we need to convert
		#each shell to a solid, and then re-create a new compound of solids
		"""
		if fixedShape.ShapeType() == TopAbs.TopAbs_COMPOUND:
	
			log.warn("Shape is a compound. Creating solids for each shell.");
			builder= BRep.BRep_Builder();
			newCompound = TopoDS.TopoDS_Compound();
			#newCompound = TopoDS.TopoDS_CompSolid();
			builder.MakeCompound(newCompound);
			#builder.MakeCompSolid(newCompound);
			for shell in Topo(fixedShape).shells():
				
				solidBuilder = BRepBuilderAPI.BRepBuilderAPI_MakeSolid(shell);
				solid = solidBuilder.Solid();
				sa = SolidAnalyzer(solid);
				print sa.friendlyDimensions();
				builder.Add(newCompound, solid);
			
			#time.sleep(4);
			#Topology.dumpTopology(newCompound);
			return newCompound;  #return temporarily after the first one
		else:
			log.info("Making Solid from the Shell...");
	
			solidBuilder = BRepBuilderAPI.BRepBuilderAPI_MakeSolid(ts.Shell(fixedShape));
			return solidBuilder.Solid();
		"""
		self.shape = fixedShape;
	
"""
	Point
"""
class Point:
	def __init__(self,point):
		self.point = point;
		
	def __str__(self):
		return "[%0.3f %0.3f %0.3f]" % (self.point.X(), self.point.Y(), self.point.Z());
		
"""
  Edge: provides useful functions for dealing with an edge
"""
class Edge:
	def __init__(self,edge):

		self.edge = edge;		
		hc = BRep.BRep_Tool().Curve(edge);
		self.curve = GeomAdaptor.GeomAdaptor_Curve(hc[0]); 
		self.handleCurve  = hc[0];
		self.firstParameter = hc[1];
		self.lastParameter = hc[2];

		p1 = self.curve.Value(self.firstParameter);
		p2 = self.curve.Value(self.lastParameter);

		#compute the first and last points, which are very commonly used		
		if edge.Orientation() == TopAbs.TopAbs_FORWARD:
			self.reversed = False;
			self.firstPoint = p1;
			self.lastPoint = p2;
		else:
			self.reversed = True;
			self.firstPoint = p2;
			self.lastPoint = p1;
	
	"returns a PointOnEdge object"
	def getPointAtVertex(self,vertex):
		p = brepTool.Parameter(vertex,self.edge);		
		r = PointOnEdge();

		r.param = p;
		r.vertex = vertex;
		r.edge = self.edge;
				
		(r.point,r.vector) = OCCUtil.D1AtPointOnCurve(self.curve,p);
		#tricky-- reverse the vector if the edge is reversed
		if self.reversed:
			r.vector = r.vector.Reversed();
		r.niceVec = Vec(r.vector);
		r.nicePoint = Pnt(r.point);			
		return r;
		
	def distanceBetweenEnds(self):
		"length of the edge, assuming it is a straight line"
		return self.firstPoint.Distance(self.lastPoint);
	
	def length(self):
		props = GProp.GProp_GProps();
		gp = BRepGProp.BRepGProp().LinearProperties(self.edge,props);
		length = props.Mass(); #really the length of an edge.
		return length;
	   
	def isLine(self):
		return self.curve.GetType() == GeomAbs.GeomAbs_Line;
	
	"""
		Deprecated, please use getPointAtParameter!
	"""
	def pointAtParameter(self,p):
		raise Exception("Please use getPointAtParamter instead, which also computes other stuff");
		"return the point corresponding to the desired parameter"
		if p < self.firstParameter or p > self.lastParameter:
			raise ValueError,"Expected parameter between first and last."
		return self.curve.Value(p);

	def splitAtParameter(self,p):
		"""
		  split this edge at the supplied parameter.
		  returns two EdgeWwrappers
		"""
		e1 = self.trimmedEdge(self.firstParameter,p);
		e2 = self.trimmedEdge(p,self.lastParameter);
		return [e1,e2];
	
	"""
		get a trimmed version of this edge between two points, projected as necessary  
		onto the underlying curve
		
		OK, the simple GeomAPI_ProjectPointOnCurve approach didnt work at all-- even for simple lines, 
		when the point was outside of the curve's range, it didnt work.
	"""
	def trimmedEdgeFromPoints(self,point1, point2,tolerance):
		print "I am %s" % self
		print "Creating new edge from points: ",Point(point1),Point(point2)
		#(param1,newPoint1) = OCCUtil.findPointOnCurve(point1,self.handleCurve,tolerance);
		#(param2,newPoint2) = OCCUtil.findPointOnCurve(point2,self.handleCurve,tolerance);
		#well this is annoying-- the parameter range appears to be preventing projection, so we need to pad them
		fp = self.firstParameter;
		fpnt = self.firstPoint;
		lp = self.lastParameter;
		lpnt = self.lastPoint;
		if fp > lp:
			(lp,fp)=(fp,lp);
			(fpnt,lpnt)=(lpnt,fpnt);
			
		print "Params: fp=%0.3f, lp=%0.3f,tolerance=%0.3f" % ( fp, lp,tolerance);

		(param1,newPoint1) = OCCUtil.findPointOnCurve(point1,self.handleCurve,tolerance);
		#check bounds by hand
		if param1 < fp: 
			param1 = fp;
			newPoint1 = fpnt;
		if param1 > lp: 
			parm1 = fp;
			newPoint1 = lpnt;
		print "point 1!"
		(param2,newPoint2) = OCCUtil.findPointOnCurve(point2,self.handleCurve,tolerance);
		if param2 < fp: 
			param2 = fp;
			newPoint2 = fpnt;
		if param2 > lp: 
			parm2 = fp;
			newPoint2 = lpnt;

		return self.trimmedEdge(param1,param2);
		
		
	def trimmedEdge(self,parameter1, parameter2):
		"make a trimmed edge based on a start and end parameter on the same curve"
		"p1 and p2 are either points or parameters"
		print "Computing new edge: p1=%0.3f, p2=%0.3f, fp=%0.3f, lp=%0.3f" % (parameter1,parameter2,self.firstParameter,self.lastParameter);
		if abs(parameter1 - parameter2) < 0.0001:
			print "WARNING: removing degenerate edge";
			return None;
		e = OCCUtil.edgeFromTwoPointsOnCurve(self.handleCurve, parameter1, parameter2 );		
		return e;
		
	def isCircle(self):
		return self.curve.GetType() == GeomAbs.GeomAbs_Circle;
	
	
	"""
		same as discretePoints, but returns a list of tuples not a generator fo gp_Pnt
	"""
	def discreteTuples(self,deflection):
		r = [];
		for p in self.discretePoints(deflection):
			r.append(( p.X(), p.Y() ) );
		return r;

	def discretePoints(self,deflection):
		"a generator for all the points on the edge, in forward order"
		gc = GCPnts.GCPnts_QuasiUniformDeflection(self.curve,deflection,self.firstParameter,self.lastParameter);
		#print "Making Dicrete Points!"
		i = 1;
		numPts = gc.NbPoints();
		while i<=numPts:
			if self.reversed:
				yield gc.Value(numPts-i+1);
			else:
				yield gc.Value(i);
			i+=1;
	
	def __str__(self):
		if self.isLine():
			s = "Line:\t";
		elif self.isCircle():
			s  = "Circle:\t";
		else:
			s = "Curve:\t"; 
		return s + str(Point(self.firstPoint)) + "-->" + str(Point(self.lastPoint));

"""
	Represents a point on an edge
	(not a vertex necessarily).
"""
class PointOnEdge():
	def __init__(self):
		self.edge = None;
		self.param = None;
		self.point = None;
		self.vector = None;
		self.edge = None;
		self.vertex = None;
		
		#TODO: remove these, they are for debug only.
		self.niceVec = None;
		self.nicePoint = None;
		
	def isVertex(self):
		return self.vertex is None;
"""
	Follow a wire's edges in order
"""
class Wire():
	def __init__(self,wire):
		self.wire = wire;
		
	def edges2(self):
		"return edges in a list"
		wireExp = BRepTools.BRepTools_WireExplorer(self.wire);
		while  wireExp.More():
			e = wireExp.Current();
			yield e;
			wireExp.Next();
		#wireExp.Clear();
	
	def edgesAsSequence(self):
		"returns edge list as a sequence"
		wireExp = BRepTools.BRepTools_WireExplorer(self.wire);
		resultWires = TopTools.TopTools_HSequenceOfShape();
		
		while  wireExp.More():
			e = wireExp.Current();
			resultWires.Append( e);
			wireExp.Next();
		
		return resultWires;
		
	def edgesAsList(self):
		edges = [];
		for e in self.edges2():
			edges.append(e);
		return edges;

	def edges(self):
		"a generator for edges"
		bb = TopExp.TopExp_Explorer();
		bb.Init(self.wire,TopAbs.TopAbs_EDGE);
		while bb.More():
			e = topoDS.edge(bb.Current());
			yield e;	
			bb.Next();		
		bb.ReInit();		
		
	def assertHeadToTail(self):
		"checks that a wire is head to tail."
		#log.info("Asserting Wire..");
		seq = self.edgesAsSequence();
		list  = listFromHSequenceOfShape(seq);
		wrapAround = self.wire.Closed();
		#if wrapAround:
			#log.info("Wire is closed.");
		for (edge1,edge2) in ntuples(list,2,wrapAround):
			ew1 = Edge(edge1);
			ew2 = Edge(edge2);
			assert ew1.lastPoint.Distance(ew2.firstPoint) < 0.0001;
		#log.info("Wire is valid.");
		
	def __str__(self):
		"print the points in a wire"
		s = ["Wire:"];
		for edge in self.edges2():
			ew = Edge(edge);
			s.append( str(ew) );
		return "\n".join(s);
		
	"""
		same as discretePoints, but returns a list of tuples not a generator fo gp_Pnt
	"""
	def discreteTuples(self,deflection):
		r = [];
		for p in self.discretePoints(deflection):
			r.append(( p.X(), p.Y() ) );
		return r;
			
	def discretePoints(self,deflection):
		"discrete points for all of a wire"
		for e in self.edges():
			for m in Edge(e).discretePoints(deflection):
				yield m;
		
if __name__=='__main__':
	print "Basic Wrappers"
	from OCC.Display.SimpleGui import *
	import TestObjects
	display, start_display, add_menu, add_function_to_menu = init_display()

	w = TestObjects.makeSquareWire();
	

	for e in Wire(w).edgesAsList():
		display.DisplayShape(e);

	start_display();

