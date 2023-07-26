import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Geom, GeomNode, GeomVertexFormat, GeomVertexData, GeomTriangles, GeomLines, GeomVertexWriter
from panda3d.core import AmbientLight, DirectionalLight, PointLight, Vec4
from panda3d.core import LVector3, LVector4
from panda3d.core import Texture, PNMImage, LColor
from panda3d.core import TransparencyAttrib
from panda3d.core import LODNode
from panda3d.core import CardMaker
from panda3d.core import loadPrcFileData
from panda3d.core import TextNode
from geopy.geocoders import Nominatim
import osmnx as ox
from geopy.exc import GeocoderTimedOut
from time import sleep
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.showbase.ShowBase import ShowBase
from shapely.geometry import Polygon
from shapely.ops import triangulate
import random

def do_geocode(geolocator, address, attempt=1, max_attempts=5):
    try:
        return geolocator.geocode(address)
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            sleep(1)  # Wait for 1 second before retrying
            return do_geocode(geolocator, address, attempt=attempt+1)
        raise

class MyApp(ShowBase):

    def __init__(self):
        loadPrcFileData("", "fullscreen true")
        loadPrcFileData("", "win-size 1920 1080")  # Set the resolution

        ShowBase.__init__(self)

        base.setFrameRateMeter(True)

        # Set the background color to black
        self.setBackgroundColor(0, 0, 0)

        self.exit_button = DirectButton(text=("Exit", "Exit", "Exit", "Exit"), 
                                        scale=.05,
                                        command=sys.exit, 
                                        pos=(-1.2, 0, 0.9), 
                                        text_align=TextNode.ALeft,
                                        frameColor=(0, 0, 0, 0),
                                        text_fg=(1, 0, 0, 1),
                                        text_shadow=(0, 0, 0, 1))

        # Get building and road data
        place_name = "Santa Monica Beach, California, USA"
        geolocator = Nominatim(user_agent="your_app_name", timeout=10)

        location = do_geocode(geolocator, place_name)

        if location:
            point = (location.latitude, location.longitude)
            tags = {"building": True}
            osm_data = ox.features_from_point(point, tags=tags, dist=750) # dist=1000
            road_data = ox.graph_from_point(point, dist=750, network_type='all')
        else:
            print("Error: Location not found")


        # Create building models and add them to the scene
        for _, building in osm_data.iterrows():
            try:
                geometry = building['geometry']
                if geometry.geom_type == 'Polygon':
                    self.create_building(geometry, location)
            except Exception as e:
                print(f"Error drawing building: {e}")

        # Create road models and add them to the scene
        for _, road_data in ox.graph_to_gdfs(road_data, nodes=False).iterrows():
            try:
                geometry = road_data['geometry']
                if geometry.geom_type == 'LineString':
                    self.create_road(geometry, location)
            except Exception as e:
                print(f"Error drawing road: {e}")

        # Set up the camera
        self.camera.set_pos(0, -50, 50)
        self.camera.set_hpr(0, -30, 0)

        # Set up lighting
        ambient_light = AmbientLight("ambientLight")
        ambient_light.setColor(LVector4(1, 1, 1, 1))
        self.render.setLight(self.render.attachNewNode(ambient_light))

        directional_light = DirectionalLight("directionalLight")
        directional_light.setDirection(LVector3(0, 8, -2.5))
        directional_light.setColor(LVector4(1, 1, 1, 1))
        self.render.setLight(self.render.attachNewNode(directional_light))


    def create_grass(self, x, y, width, height):
        # Create a green plane
        grass = GeomNode('grass')
        grass_node = self.render.attachNewNode(grass)
        grass_node.setColor(0, 1, 0, 1)  # green color

        # Set the position and scale of the plane
        grass_node.setPos(x * 100000, y * 100000, 0)
        grass_node.setScale(width * 100000, height * 100000, 1)


    def create_street_lamp(self, x, y):
        # Create a tall, thin rectangle for the lamp post
        cm = CardMaker('lamp_post')
        cm.setFrame(-0.05, 0.05, 0, 1)  # create a rectangle
        lamp_post = self.render.attachNewNode(cm.generate())
        lamp_post.setPos(x * 100000, y * 100000, 0.5)
        lamp_post.setColor(0.5, 0.5, 0.5, 1)  # gray color

        # Create a small sphere for the lamp
        lamp = self.loader.loadModel('models/smiley')
        lamp.reparentTo(self.render)
        lamp.setScale(0.05)
        lamp.setPos(x * 100000, y * 100000, 1)

        # Create a point light at the position of the lamp
        point_light = PointLight('point_light')
        point_light.setColor(Vec4(1, 1, 1, 1))
        plnp = lamp.attachNewNode(point_light)
        self.render.setLight(plnp)

    def create_traffic_light(self, x, y):
        # Create a thin rectangle for the traffic light
        cm = CardMaker('traffic_light')
        cm.setFrame(-0.05, 0.05, 0, 0.3)  # create a rectangle
        traffic_light = self.render.attachNewNode(cm.generate())
        traffic_light.setPos(x * 100000, y * 100000, 0.5)
        traffic_light.setColor(0, 0, 0, 1)  # black color

        # Create small spheres for the lights
        red_light = self.loader.loadModel('models/smiley')
        red_light.reparentTo(self.render)
        red_light.setScale(0.02)
        red_light.setPos(x * 100000, y * 100000, 0.6)
        red_light.setColor(1, 0, 0, 1)  # red

        yellow_light = self.loader.loadModel('models/smiley')
        yellow_light.reparentTo(self.render)
        yellow_light.setScale(0.02)
        yellow_light.setPos(x * 100000, y * 100000, 0.5)
        yellow_light.setColor(1, 1, 0, 1)  # yellow

        green_light = self.loader.loadModel('models/smiley')
        green_light.reparentTo(self.render)
        green_light.setScale(0.02)
        green_light.setPos(x * 100000, y * 100000, 0.4)
        green_light.setColor(0, 1, 0, 1)  # green

    def create_building(self, polygon, location):
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData('vertices', format, Geom.UHStatic)

        # Vertices for the building walls
        vdata.setNumRows(len(polygon.exterior.coords) * 2)

        vertex = GeomVertexWriter(vdata, 'vertex')
        for x, y in polygon.exterior.coords[:-1]:
            x, y = x - location.longitude, y - location.latitude
            vertex.addData3(x * 100000, y * 100000, 0)
            vertex.addData3(x * 100000, y * 100000, 10 * 10)

        prim = GeomTriangles(Geom.UHStatic)
        for i in range(0, len(polygon.exterior.coords) - 1):
            prim.addVertices(i * 2, i * 2 + 1, (i * 2 + 2) % (len(polygon.exterior.coords) * 2 - 2))
            prim.addVertices(i * 2 + 1, (i * 2 + 3) % (len(polygon.exterior.coords) * 2 - 2), (i * 2 + 2) % (len(polygon.exterior.coords) * 2 - 2))

        geom = Geom(vdata)
        geom.addPrimitive(prim)

        node = GeomNode('gnode')
        node.addGeom(geom)

        # Create the roof
        roof_coords = [(x - location.longitude, y - location.latitude) for x, y in polygon.exterior.coords[:-1]]
        roof_polygon = Polygon(roof_coords)
        triangles = triangulate(roof_polygon)
        
        # Vertices and triangles for the roof
        vdata_roof = GeomVertexData('vertices', format, Geom.UHStatic)
        vertex_roof = GeomVertexWriter(vdata_roof, 'vertex')
        prim_roof = GeomTriangles(Geom.UHStatic)

        for triangle in triangles:
            for x, y in triangle.exterior.coords[:-1]:
                vertex_roof.addData3(x * 100000, y * 100000, 10 * 10)

            start = vdata_roof.getNumRows() - 3
            prim_roof.addVertices(start, start + 1, start + 2)

        geom_roof = Geom(vdata_roof)
        geom_roof.addPrimitive(prim_roof)

        node_roof = GeomNode('gnode')
        node_roof.addGeom(geom_roof)

        # Create a random blue color
        r, g, b = random.uniform(0, 0.5), random.uniform(0.5, 1), random.uniform(0.5, 1)

        # Create a semi-transparent texture
        image = PNMImage(1, 1)
        image.setXelA(0, 0, LColor(r, g, b, 0.5))  # set the color to random blue and alpha to 0.5
        texture = Texture()
        texture.load(image)

        # Set building color to random blue
        building_node = self.render.attachNewNode(node)
        building_node.setColor(r, g, b, 1)
        building_node.setTexture(texture, 1)
        building_node.setTransparency(TransparencyAttrib.MAlpha)

        # Set roof color to random blue
        roof_node = self.render.attachNewNode(node_roof)
        roof_node.setColor(r, g, b, 1)
        roof_node.setTexture(texture, 1)
        roof_node.setTransparency(TransparencyAttrib.MAlpha)

        print("Building node created and colored")


        # Create windows
        window_color = (0.8, 0.8, 0.8, 1)
        window_width, window_height = 1, 2

        lod_node = LODNode('lod')
        lod = building_node.attachNewNode(lod_node)
        lod_node.addSwitch(500, 200)  # Less detailed windows between 200 and 500 units
        lod_node.addSwitch(200, 0)    # Detailed windows up to 200 units

        for detail, z_step in [(0, window_height * 4), (1, window_height * 2)]:
            windows_node = lod.attachNewNode('windows')
            windows_node.setColor(*window_color)

            vdata_windows = GeomVertexData('vertices', format, Geom.UHStatic)
            vertex_windows = GeomVertexWriter(vdata_windows, 'vertex')
            geom_windows = Geom(vdata_windows)

            for x, y in polygon.exterior.coords[:-1]:
                x, y = x - location.longitude, y - location.latitude

                for z in range(0, 10 * 10, z_step):
                    start = vdata_windows.getNumRows()
                    vertex_windows.addData3(x * 100000 + window_width / 2, y * 100000, z)
                    vertex_windows.addData3(x * 100000 + window_width / 2, y * 100000, z + window_height)
                    vertex_windows.addData3(x * 100000 - window_width / 2, y * 100000, z + window_height)
                    vertex_windows.addData3(x * 100000 - window_width / 2, y * 100000, z)

                    prim_window = GeomTriangles(Geom.UHStatic)
                    prim_window.addVertices(start, start + 1, start + 2)
                    prim_window.addVertices(start + 2, start + 3, start)

                    geom_windows.addPrimitive(prim_window)

            node_windows = GeomNode('gnode')
            node_windows.addGeom(geom_windows)
            windows_node.attachNewNode(node_windows)

        print("Windows created")

        
    def create_window(self, x, y, z, width, height):
        format = GeomVertexFormat.getV3()
        vdata = GeomVertexData('vertices', format, Geom.UHStatic)
        vdata.setNumRows(4)

        vertex = GeomVertexWriter(vdata, 'vertex')
        vertex.addData3(x * 100000 + width / 2, y * 100000, z)
        vertex.addData3(x * 100000 + width / 2, y * 100000, z + height)
        vertex.addData3(x * 100000 - width / 2, y * 100000, z + height)
        vertex.addData3(x * 100000 - width / 2, y * 100000, z)

        prim = GeomTriangles(Geom.UHStatic)
        prim.addVertices(0, 1, 2)
        prim.addVertices(2, 3, 0)

        geom = Geom(vdata)
        geom.addPrimitive(prim)

        node = GeomNode('gnode')
        node.addGeom(geom)

        window_node = self.render.attachNewNode(node)
        return window_node

    def create_road(self, line, location):
        format = GeomVertexFormat.getV3()
        vdata= GeomVertexData('vertices', format, Geom.UHStatic)
        vdata.setNumRows(len(line.coords))

        vertex = GeomVertexWriter(vdata, 'vertex')

        for x, y in line.coords:
            # Convert coordinates to a local coordinate system
            x, y = x - location.longitude, y - location.latitude
            vertex.addData3(x * 100000, y * 100000, 0.1)

        prim = GeomLines(Geom.UHStatic)
        for i in range(len(line.coords) - 1):
            prim.addVertices(i, i + 1)

        geom = Geom(vdata)
        geom.addPrimitive(prim)

        node = GeomNode('gnode')
        node.addGeom(geom)

        # Set road color to white
        road_node = self.render.attachNewNode(node)
        road_node.setColor(1, 1, 1, 1)

        # Set the road width
        road_node.setRenderModeThickness(2)

        # Create street lamps and traffic lights along the road
        for i, (x, y) in enumerate(line.coords):
            # Convert coordinates to a local coordinate system
            x, y = x - location.longitude, y - location.latitude

            # Create a street lamp at every 5th point
            if i % 5 == 0:
                self.create_street_lamp(x, y)

            # Create a traffic light at every 10th point
            if i % 10 == 0:
                self.create_traffic_light(x, y)

app = MyApp()
app.run()