from tkinter import *
import xml.dom.minidom
import exifread
from tkinter.filedialog import askopenfilenames
import PIL
from PIL import Image
from zipfile import ZipFile
import os
import os.path
import shutil


class Application(Frame):

    def __init__(self, master):

        Frame.__init__(self, master)
        self.grid()
        self.create_widgets()

    def create_widgets(self):

        #SETUP MENU STRUCTURE
        menubar = Menu(root)

        #SETUP FILE MENU
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        selectmenu = Menu(menubar, tearoff=0)
        selectmenu.add_command(label="Select Images", command= self.select_imgs)
        menubar.add_cascade(label="Select Images", menu=selectmenu)

        aboutmenu = Menu(menubar, tearoff=0)
        aboutmenu.add_command(label="About", command= self.show_about)
        menubar.add_cascade(label="About", menu=aboutmenu)

        #ADD MENUBAR TO CONFIG
        root.config(menu=menubar)

        self.savekmz = IntVar()
        self.savekmz.set(1)
        self.checkbuttonC = Checkbutton(self, text="Save as KMZ?", variable=self.savekmz)
        self.checkbuttonC.grid(row = 1, column = 1, columnspan = 1, sticky = W )

        self.status = Label(root, fg='green')
        self.status.grid(row=1, column=0)
        self.status['text'] = "Select GPS Tagged .JPG Images"

        self.selectedImgs = []

    def show_about(self):

        ABOUT_TEXT = """GeoTag 1.2

        Released 5/31/16
        Email: David@rankinstudio.com

        1. Take images with smart phone using GPS feature in camera
        2. Save .jpg images to computer
        3. Open images with this program
            (Images will be resized to 1000px wide
            for better performance)
        4. Open "TaggedImgs.kml" with Google Earth
        5. Click on camera icons to open images in Google Earth

        Check "Save as KMZ?" if you would like to make an archive
        you can share with others easily.

        Enjoy!"""

        toplevel = Toplevel()
        toplevel.resizable(width=FALSE, height=FALSE)
        toplevel.title('About')
        label1 = Label(toplevel, text=ABOUT_TEXT, height=0, width=50, justify=LEFT)
        label1.grid()

    def GetFile(self, file_name):

        the_file = None

        try:
            the_file = open(file_name, 'rb')

        except IOError:
            the_file = None

        return the_file

    def GetHeaders(self, the_file):
        data = exifread.process_file(the_file, 'UNDEF', False, False, False)
        return data

    def DmsToDecimal(slef, degree_num, degree_den, minute_num, minute_den, second_num, second_den):

        degree = float(degree_num)/float(degree_den)
        minute = float(minute_num)/float(minute_den)/60
        second = float(second_num)/float(second_den)/3600
        return degree + minute + second

    def GetGps(self, data):

        lat_dms = data['GPS GPSLatitude'].values
        long_dms = data['GPS GPSLongitude'].values
        latitude = self.DmsToDecimal(lat_dms[0].num, lat_dms[0].den,
                              lat_dms[1].num, lat_dms[1].den,
                              lat_dms[2].num, lat_dms[2].den)
        longitude = self.DmsToDecimal(long_dms[0].num, long_dms[0].den,
                               long_dms[1].num, long_dms[1].den,
                               long_dms[2].num, long_dms[2].den)
        if data['GPS GPSLatitudeRef'].printable == 'S': latitude *= -1
        if data['GPS GPSLongitudeRef'].printable == 'W': longitude *= -1
        altitude = None

        try:
            alt = data['GPS GPSAltitude'].values[0]
            altitude = alt.num/alt.den
            if data['GPS GPSAltitudeRef'] == 1: altitude *= -1

        except KeyError:
            altitude = 0

        return latitude, longitude, altitude

    def CreateKmlDoc(self):
        """Creates a KML document."""

        kml_doc = xml.dom.minidom.Document()
        kml_element = kml_doc.createElementNS('http://www.opengis.net/kml/2.2', 'kml')
        kml_element.setAttribute('xmlns', 'http://www.opengis.net/kml/2.2')
        kml_element = kml_doc.appendChild(kml_element)
        document = kml_doc.createElement('Document')
        kml_element.appendChild(document)
        return kml_doc

    def CreatePhotoOverlay(self, kml_doc, file_name, the_file, file_iterator):

        document = kml_doc.getElementsByTagName('Document')[0]
        photo_id = 'photo%s' % file_iterator
        data = self.GetHeaders(the_file)
        coords = self.GetGps(data)

        name = kml_doc.createElement('name')
        name.appendChild(kml_doc.createTextNode(file_name))
        document.appendChild(name)

        open = kml_doc.createElement('open')
        styleid = kml_doc.createElement('Style')
        styleid.setAttribute('id',"camera")
        iconstyle = kml_doc.createElement('IconStyle')
        styicon = kml_doc.createElement('Icon')
        iconhref= kml_doc.createElement('href')

        styleid.appendChild(iconstyle)
        iconstyle.appendChild(styicon)
        styicon.appendChild(iconhref)
        iconhref.appendChild(kml_doc.createTextNode(':/camera_mode.png')) #change for local icon cicon.png :/camera_mode.png


        open.appendChild(kml_doc.createTextNode('1'))
        document.appendChild(open)
        document.appendChild(styleid)

        po = kml_doc.createElement('PhotoOverlay')
        po.setAttribute('id', photo_id)

        name2 = kml_doc.createElement('name')
        name2.appendChild(kml_doc.createTextNode(file_name.split('/')[-1]))
        po.appendChild(name2)

        icon = kml_doc.createElement('Icon')
        href = kml_doc.createElement('href')
        href.appendChild(kml_doc.createTextNode(file_name))
        camera = kml_doc.createElement('Camera')
        longitude = kml_doc.createElement('longitude')
        latitude = kml_doc.createElement('latitude')
        altitude = kml_doc.createElement('altitude')
        heading = kml_doc.createElement('heading')
        tilt = kml_doc.createElement('tilt')
        roll = kml_doc.createElement('roll')
        # Determines the proportions of the image and uses them to set FOV.
        width = float(data['EXIF ExifImageWidth'].printable)
        length = float(data['EXIF ExifImageLength'].printable)
        lf = str(width/length * -20.0)
        rf = str(width/length * 20.0)
        styleurl = kml_doc.createElement('styleUrl')
        styleurl.appendChild(kml_doc.createTextNode('#camera'))

        longitude.appendChild(kml_doc.createTextNode(str(coords[1])))
        latitude.appendChild(kml_doc.createTextNode(str(coords[0])))
        altitude.appendChild(kml_doc.createTextNode('5'))
        tilt.appendChild(kml_doc.createTextNode('90'))
        heading.appendChild(kml_doc.createTextNode('0'))
        roll.appendChild(kml_doc.createTextNode('0'))
        camera.appendChild(longitude)
        camera.appendChild(latitude)
        camera.appendChild(altitude)
        camera.appendChild(heading)
        camera.appendChild(tilt)
        camera.appendChild(roll)
        icon.appendChild(href)
        viewvolume = kml_doc.createElement('ViewVolume')
        leftfov = kml_doc.createElement('leftFov')
        rightfov = kml_doc.createElement('rightFov')
        bottomfov = kml_doc.createElement('bottomFov')
        topfov = kml_doc.createElement('topFov')
        near = kml_doc.createElement('near')
        leftfov.appendChild(kml_doc.createTextNode(lf))
        rightfov.appendChild(kml_doc.createTextNode(rf))
        bottomfov.appendChild(kml_doc.createTextNode('-20'))
        topfov.appendChild(kml_doc.createTextNode('20'))
        near.appendChild(kml_doc.createTextNode('5'))
        viewvolume.appendChild(leftfov)
        viewvolume.appendChild(rightfov)
        viewvolume.appendChild(bottomfov)
        viewvolume.appendChild(topfov)
        viewvolume.appendChild(near)
        po.appendChild(camera)
        po.appendChild(styleurl)
        po.appendChild(icon)
        po.appendChild(viewvolume)
        point = kml_doc.createElement('Point')
        coordinates = kml_doc.createElement('coordinates')
        coordinates.appendChild(kml_doc.createTextNode('%s,%s,%s' %(coords[1],
                                                                    coords[0],
                                                                    coords[2])))
        point.appendChild(coordinates)
        po.appendChild(point)

        document.appendChild(po)

    def CreatePhotoOverlayKMZ(self, kml_doc, file_name, the_file, file_iterator):

        filedir = 'files'
        document = kml_doc.getElementsByTagName('Document')[0]
        photo_id = 'photo%s' % file_iterator
        data = self.GetHeaders(the_file)
        coords = self.GetGps(data)

        name = kml_doc.createElement('name')
        name.appendChild(kml_doc.createTextNode(file_name.split('/')[-1])) #UPDATED
        document.appendChild(name)

        open = kml_doc.createElement('open')
        styleid = kml_doc.createElement('Style')
        styleid.setAttribute('id',"camera")
        iconstyle = kml_doc.createElement('IconStyle')
        styicon = kml_doc.createElement('Icon')
        iconhref= kml_doc.createElement('href')

        styleid.appendChild(iconstyle)
        iconstyle.appendChild(styicon)
        styicon.appendChild(iconhref)
        iconhref.appendChild(kml_doc.createTextNode(':/camera_mode.png')) #change for local icon cicon.png :/camera_mode.png
        # iconhref.appendChild(kml_doc.createTextNode('cicon.png')) #change for local icon cicon.png :/camera_mode.png


        open.appendChild(kml_doc.createTextNode('1'))
        document.appendChild(open)
        document.appendChild(styleid)

        po = kml_doc.createElement('PhotoOverlay')
        po.setAttribute('id', photo_id)

        name2 = kml_doc.createElement('name')
        name2.appendChild(kml_doc.createTextNode(file_name.split('/')[-1]))
        po.appendChild(name2)

        icon = kml_doc.createElement('Icon')
        href = kml_doc.createElement('href')
        href.appendChild(kml_doc.createTextNode(filedir +'/'+ file_name.split('/')[-1]))
        camera = kml_doc.createElement('Camera')
        longitude = kml_doc.createElement('longitude')
        latitude = kml_doc.createElement('latitude')
        altitude = kml_doc.createElement('altitude')
        heading = kml_doc.createElement('heading')
        tilt = kml_doc.createElement('tilt')
        roll = kml_doc.createElement('roll')
        # Determines the proportions of the image and uses them to set FOV.
        width = float(data['EXIF ExifImageWidth'].printable)
        length = float(data['EXIF ExifImageLength'].printable)
        lf = str(width/length * -20.0)
        rf = str(width/length * 20.0)
        styleurl = kml_doc.createElement('styleUrl')
        styleurl.appendChild(kml_doc.createTextNode('#camera'))

        longitude.appendChild(kml_doc.createTextNode(str(coords[1])))
        latitude.appendChild(kml_doc.createTextNode(str(coords[0])))
        altitude.appendChild(kml_doc.createTextNode('5'))
        tilt.appendChild(kml_doc.createTextNode('90'))
        heading.appendChild(kml_doc.createTextNode('0'))
        roll.appendChild(kml_doc.createTextNode('0'))
        camera.appendChild(longitude)
        camera.appendChild(latitude)
        camera.appendChild(altitude)
        camera.appendChild(heading)
        camera.appendChild(tilt)
        camera.appendChild(roll)
        icon.appendChild(href)
        viewvolume = kml_doc.createElement('ViewVolume')
        leftfov = kml_doc.createElement('leftFov')
        rightfov = kml_doc.createElement('rightFov')
        bottomfov = kml_doc.createElement('bottomFov')
        topfov = kml_doc.createElement('topFov')
        near = kml_doc.createElement('near')
        leftfov.appendChild(kml_doc.createTextNode(lf))
        rightfov.appendChild(kml_doc.createTextNode(rf))
        bottomfov.appendChild(kml_doc.createTextNode('-20'))
        topfov.appendChild(kml_doc.createTextNode('20'))
        near.appendChild(kml_doc.createTextNode('5'))
        viewvolume.appendChild(leftfov)
        viewvolume.appendChild(rightfov)
        viewvolume.appendChild(bottomfov)
        viewvolume.appendChild(topfov)
        viewvolume.appendChild(near)
        po.appendChild(camera)
        po.appendChild(styleurl)
        po.appendChild(icon)
        po.appendChild(viewvolume)
        point = kml_doc.createElement('Point')
        coordinates = kml_doc.createElement('coordinates')
        coordinates.appendChild(kml_doc.createTextNode('%s,%s,%s' %(coords[1],
                                                                    coords[0],
                                                                    coords[2])))
        point.appendChild(coordinates)
        po.appendChild(point)

        document.appendChild(po)

    def CreateKmlFile(self, file_names, new_file_name):

        files = {}

        for file_name in file_names:
            the_file = self.GetFile(file_name)
            if the_file is None:
                print("'%s' is unreadable\n" % file_name)
                file_names.remove(file_name)
                continue
            else:
                files[file_name] = the_file

        kml_doc = self.CreateKmlDoc()
        file_iterator = 0

        try:

            for key in files.keys():
                if self.savekmz.get() == 1:
                    self.CreatePhotoOverlayKMZ(kml_doc, key, files[key], file_iterator)
                    file_iterator += 1
                else:
                    self.CreatePhotoOverlay(kml_doc, key, files[key], file_iterator)
                    file_iterator += 1

        except TypeError:
            self.status['text'] = "ERROR: NO GPS Data in Image"
            self.update()


        kml_file = open(new_file_name, 'wb')
        kml_file.write(kml_doc.toprettyxml('  ', newl='\n', encoding='utf-8'))

    def converttokmz(self, files):

        dest1 = os.getcwd()
        dest2 = "TaggedShare"
        dest3 = "files"
        saveto1 = os.path.join(dest1, dest2, dest3)
        saveto2 = os.path.join(dest1, dest2)

        if os.path.isdir(saveto1): #chcek to see if image path already exists
            print("Path Exists")
        else:
            os.makedirs(saveto1)

        for file in files:
            shutil.copy2(file, saveto1)

        kmlfile = dest1 + "/" + 'TaggedImgs.kml'

        shutil.copy2(kmlfile, saveto2)

        kmltorename = dest1 + "/" + dest2 + "/" + 'TaggedImgs.kml'
        kmlnewname = dest1 + "/" + dest2 + "/" + 'doc.kml'

        if os.path.isfile(kmlnewname):
            os.remove(kmlnewname)

        os.rename(kmltorename, kmlnewname)

        tozip = dest1 +"/"+ dest2
        zipfile = dest1 +"/"+ dest2
        shutil.make_archive(zipfile, 'zip', tozip)

        shutil.rmtree(tozip) #NEMOVE DIR USED TO MAKE ZIP


        #RENAME ZIP TO KMZ
        ziptorename = dest1 + "/TaggedShare.zip"
        ziptokmz = dest1 + "/TaggedShare.kmz"

        if os.path.isfile(ziptokmz):
            os.remove(ziptokmz)

        os.rename(ziptorename, ziptokmz)

        #CLEAN UP
        if os.path.isfile(kmlfile):
            os.remove(kmlfile)


        self.status['text'] = "Saved TaggedShare.KMZ"
        self.update()

    def select_imgs(self):
        # try:
        self.selectedImgs = askopenfilenames()

        if len(self.selectedImgs) == 0:
            self.status['text'] = "ERROR: Nothing Selected"
            self.update()
            return

        for i in self.selectedImgs:
            filetype = i.split('.')[-1] #SPLIT OUT NAME FROM LEFT
            if filetype != 'jpg':
                self.status['text'] = "ERROR: Select JPG Images"
                self.update()
                self.selectedImgs= []
                return
            else:
                self.status['text'] = "Creating KML File..."
                self.update()


        self.status['text'] = 'Resizing Images, Please Wait...'
        self.update()

        for n in self.selectedImgs:
            basewidth = 1000
            img = Image.open(n)
            wpercent = (basewidth/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            exif = img.info['exif']
            img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
            img.save(n, exif=exif)

        self.CheckGPS(self.selectedImgs)

        # except OSError as e:
        #     self.status['text'] = "Error: Try Again"
        #     self.update()
        #     return

    def CheckGPS(self, file_names):

        #CHECK SOME GPS SHIT YEAH
        self.status['text'] = "Checking for GPS Tags..."
        self.update()

        self.selectedImgsUpdated = []

        for n in range(len(file_names)):

            the_file = open(file_names[n], 'rb')

            data = self.GetHeaders(the_file)

            if 'GPS GPSLatitude' in data:
                self.status['text'] = "FOUND GPS"
                self.update()
                self.selectedImgsUpdated.append(file_names[n])
            else:
                self.status['text'] = "NO GPS"
                self.update()

        if len(self.selectedImgsUpdated) == 0:
            self.status['text'] = "ERROR: No GPS Data Found"
            self.update()
            return
        else:
            self.FireMake()

    def FireMake(self):
        self.CreateKmlFile(self.selectedImgsUpdated, 'TaggedImgs.kml')
        self.status['text'] = "Saved TaggedImgs.kml"
        self.update()


        #INSERT AFTER SAVE OPTOINS HERE
        if self.savekmz.get() == 1: #CONVERT TO PNG RETURNS TRUE
            self.status['text'] = 'Converting to KMZ'
            self.update()
            self.converttokmz(self.selectedImgsUpdated)


root = Tk()
root.title("GeoTag")
root.geometry("210x53")
app = Application(root)
root.resizable(width=FALSE, height=FALSE)
root.mainloop()