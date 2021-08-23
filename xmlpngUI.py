import sys
from PIL.ImageQt import QImage
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QResizeEvent
from PyQt5.QtWidgets import QAction, QApplication, QCheckBox, QFormLayout, QFrame, QGridLayout, QInputDialog, QLineEdit, QMainWindow, QMessageBox, QProgressDialog, QPushButton, QSpacerItem, QWidget, QLabel, QFileDialog
from PyQt5 import uic
import ntpath

from PyQt5.sip import setdeleted

import xmlpngengine

from time import sleep

SPRITEFRAME_SIZE = 130
MAGIC_SLEEP_TIME = 0.5

class FrameAdjustWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adjust FrameX and FrameY")
        self.setFixedSize(500, 300)
        formlayout = QFormLayout()

        self.lab1 = QLabel("FrameX: ", self)
        self.frame_x_input = QLineEdit(self)
        self.frame_x_input.setText("0")

        self.lab2 = QLabel("FrameY: ", self)
        self.frame_y_input = QLineEdit(self)
        self.frame_y_input.setText("0")

        self.lab3 = QLabel("Frame Width: ", self)
        self.frame_w_input = QLineEdit(self)
        self.frame_w_input.setText("default")

        self.lab4 = QLabel("Frame Height: ", self)
        self.frame_h_input = QLineEdit(self)
        self.frame_h_input.setText("default")

        self.submitbtn = QPushButton("Set FrameX and FrameY", self)

        # self.warnlabel = QLabel("Warning: If 'clip all to checkbox' option is selected then these options will be overwritten!")

        formlayout.addWidget(self.lab1)
        formlayout.addWidget(self.frame_x_input)
        formlayout.addWidget(self.lab2)
        formlayout.addWidget(self.frame_y_input)
        formlayout.addWidget(self.lab3)
        formlayout.addWidget(self.frame_w_input)
        formlayout.addWidget(self.lab4)
        formlayout.addWidget(self.frame_h_input)
        formlayout.addWidget(self.submitbtn)
        # formlayout.addWidget(self.warnlabel)

        self.setLayout(formlayout)

class SpriteFrame(QWidget):
    def __init__(self, imgpath, parent, imdat: QImage = None, posename: str = None):
        super().__init__()
        self.imgpath = imgpath
        self.imdat = imdat
        self.from_single_png = not imdat
        self.image_pixmap = QPixmap(imgpath) if self.from_single_png else QPixmap.fromImage(imdat)
        self.pose_name = "idle" if self.from_single_png else " ".join((posename[:-4]).split(' ')[1:]) # I'm assuming the character name is just the first word
        self.myframe = QFrame(self)
        self.framex = self.framey = self.framew = self.frameh = None

        self.img_label = QLabel(self.myframe)

        if self.from_single_png:
            self.img_label.setToolTip(self.get_tooltip_string(parent))
        else:
            ttstring = f"Image:(part of) {ntpath.basename(imgpath)}\n" + \
                f"Current Pose: {self.pose_name}\n" + \
                f"Will appear in XML as:\n\t<SubTexture name=\"{posename}\" (...) >\n\t# = digit from 0-9"
            self.img_label.setToolTip(ttstring)


        self.img_label.setPixmap(self.image_pixmap.scaled(128, 128))

        self.setFixedSize(QSize(SPRITEFRAME_SIZE, SPRITEFRAME_SIZE))

        self.remove_btn = QPushButton(self.myframe)
        self.remove_btn.move(90, 90)
        self.remove_btn.setIcon(QIcon('./image-assets/remove-frame-icon.svg'))
        self.remove_btn.setIconSize(QSize(40, 40))
        self.remove_btn.setFixedSize(40, 40)
        self.remove_btn.setToolTip("Delete Frame")
        self.remove_btn.clicked.connect(lambda: self.remove_self(parent))

        self.select_checkbox = QCheckBox(self.myframe)
        self.select_checkbox.move(5, 5)
        self.select_checkbox.stateChanged.connect(lambda : self.add_to_selected_arr(parent))

        self.myframe.setStyleSheet("QFrame{border-style:solid; border-color:black; border-width:2px}")
    
    # overriding the default mousePressEvent
    def mousePressEvent(self, event):
        btnpressed = event.button()
        if btnpressed == 1: # left mouse button
            prevstate = self.select_checkbox.checkState()
            newstate = 0 if prevstate != 0 else 1
            self.select_checkbox.setChecked(newstate)
        else:
            print("Click with the left mouse button")
    
    # overriding the default enterEvent
    def enterEvent(self, event):
        self.myframe.setStyleSheet("QFrame{ border-style:solid; border-color:#FFC9DEF5; border-width:4px }")
    
    # overriding the default leaveEvent
    def leaveEvent(self, event):
        self.myframe.setStyleSheet("QFrame{border-style:solid; border-color:black; border-width:2px}")
    
    def remove_self(self, parent):
        parent.labels.remove(self)
        if self in parent.selected_labels:
            parent.selected_labels.remove(self)
        parent.num_labels -= 1

        parent.frames_layout.removeWidget(self)
        self.deleteLater()

        parent.re_render_grid()
        print("Deleting image, count: ", parent.num_labels, "Len of labels", len(parent.labels))
        if len(parent.labels) == 0:
            parent.posename_btn.setDisabled(True)
    
    def add_to_selected_arr(self, parent):
        if self.select_checkbox.checkState() == 0:
            parent.selected_labels.remove(self)
        else:
            parent.selected_labels.append(self)
        
        parent.actionEdit_Frame_Properties.setDisabled(len(parent.selected_labels) <= 0)
    
    def get_tooltip_string(self, parent):
        charname:str = parent.charname_textbox.text()
        charname = charname.strip() if charname.strip() != "" else "[ENTER YOUR CHARACTER NAME]"
        inside_subtex_name = f"{charname} {self.pose_name}####"

        ttstring = f"Image:{ntpath.basename(self.imgpath)}\n" + \
        f"Current Pose: {self.pose_name}\n" + \
        f"Will appear in XML as:\n\t<SubTexture name=\"{inside_subtex_name}\" (...) >\n\t# = digit from 0-9"
        return ttstring


def display_progress_bar(parent, title="Sample text", startlim=0, endlim=100):
    def update_prog_bar(progress, filename):
        progbar.setValue(progress)
        progbar.setLabel(QLabel(f"Adding: {filename}"))
    progbar = QProgressDialog(title, None, startlim, endlim, parent)
    progbar.setWindowModality(Qt.WindowModal)
    progbar.show()

    return update_prog_bar, progbar

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('NewXMLPngUI.ui', self)
        self.setWindowTitle("XML Generator")

        self.generatexml_btn.clicked.connect(self.generate_xml)
        self.frames_area.setWidgetResizable(True)
        self.frames_layout = QGridLayout(self.sprite_frame_content)
        self.frames_area.setWidget(self.sprite_frame_content)

        self.num_labels = 0
        self.labels = []
        self.selected_labels = []

        self.add_img_button = QPushButton()
        self.add_img_button.setIcon(QIcon("./image-assets/AddImg.png"))
        self.add_img_button.setGeometry(0, 0, SPRITEFRAME_SIZE, SPRITEFRAME_SIZE)
        self.add_img_button.setFixedSize(QSize(SPRITEFRAME_SIZE, SPRITEFRAME_SIZE))
        self.add_img_button.setIconSize(QSize(SPRITEFRAME_SIZE, SPRITEFRAME_SIZE))
        self.add_img_button.clicked.connect(self.open_file_dialog)

        self.frames_layout.addWidget(self.add_img_button, 0, 0, Qt.AlignmentFlag(0x1|0x20))
        self.myTabs.setCurrentIndex(0)

        self.setWindowIcon(QIcon("./image-assets/appicon.png"))
        self.icongrid_zoom = 1
        self.uploadicongrid_btn.clicked.connect(self.uploadIconGrid)
        self.generateicongrid_btn.clicked.connect(self.getNewIconGrid)
        self.uploadicons_btn.clicked.connect(self.appendIcon)

        self.action_zoom_in = QAction(self.icongrid_holder_label)
        self.icongrid_holder_label.addAction(self.action_zoom_in)
        self.action_zoom_in.triggered.connect(self.zoomInPixmap)
        self.action_zoom_in.setShortcut("Ctrl+i")

        self.action_zoom_out = QAction(self.icongrid_holder_label)
        self.icongrid_holder_label.addAction(self.action_zoom_out)
        self.action_zoom_out.triggered.connect(self.zoomOutPixmap)
        self.action_zoom_out.setShortcut("Ctrl+o")

        self.zoom_label.setText("Zoom: 100%")

        self.iconpaths:list = []
        self.icongrid_path:str = ""

        self.posename_btn.clicked.connect(self.setAnimationNames)
        self.posename_btn.setDisabled(True)
        self.charname_textbox.textChanged.connect(self.onCharacterNameChange)

        self.num_cols = 6
        self.num_rows = 1

        self.actionImport_Images.triggered.connect(self.open_file_dialog)
        self.action_import_existing.triggered.connect(self.open_existing_spsh_xml)

        self.num_rows = 1 + self.num_labels//self.num_cols
        
        for i in range(self.num_cols):
            self.frames_layout.setColumnMinimumWidth(i, 0)
            self.frames_layout.setColumnStretch(i, 0)
        for i in range(self.num_rows):
            self.frames_layout.setRowMinimumHeight(i, 0)
            self.frames_layout.setRowStretch(i, 0)
        
        vspcr = QSpacerItem(1, 1)
        self.frames_layout.addItem(vspcr, self.num_rows, 0, 1, 4)

        hspcr = QSpacerItem(1, 1)
        self.frames_layout.addItem(hspcr, 0, self.num_cols, self.num_rows, 1)

        self.actionClear_Spritesheet_Grid.triggered.connect(self.clear_spriteframe_grid)
        self.myTabs.currentChanged.connect(self.handle_tab_change)
        self.actionEdit_Frame_Properties.triggered.connect(self.edit_frame_handler)
        self.actionEdit_Frame_Properties.setDisabled(True)
    
    def edit_frame_handler(self):
        self.framexy_window = FrameAdjustWindow()
        self.framexy_window.submitbtn.clicked.connect(self.get_frame_stuff)
        self.framexy_window.show()
    
    def get_frame_stuff(self):
        self.framexy_window.close()
        try:
            fx = int(self.framexy_window.frame_x_input.text())
            fy = int(self.framexy_window.frame_y_input.text())
            fw = self.framexy_window.frame_w_input.text()
            fh = self.framexy_window.frame_h_input.text()
            for sel_lab in self.selected_labels:
                sel_lab.framex = fx
                sel_lab.framey = fy
                sel_lab.framew = fw if fw == 'default' else int(fw)
                sel_lab.frameh = fh if fh == 'default' else int(fh)
            
            for label in list(self.selected_labels):
                label.select_checkbox.setChecked(False)
        except ValueError:
            self.display_msg_box(
                window_title="Error!",
                text="One of the values you entered was an invalid integer!",
                icon=QMessageBox.Critical
            )

    def handle_tab_change(self, newtabind):
        if newtabind != 0:
            self.actionClear_Spritesheet_Grid.setDisabled(True)
            self.action_import_existing.setDisabled(True)
            self.actionImport_Images.setDisabled(True)
        else:
            self.actionClear_Spritesheet_Grid.setDisabled(False)
            self.action_import_existing.setDisabled(False)
            self.actionImport_Images.setDisabled(False)
    
    def onCharacterNameChange(self):
        for label in self.labels:
            label.img_label.setToolTip(label.get_tooltip_string(self))
    
    def clear_spriteframe_grid(self):
        labs = list(self.labels)
        for lab in labs:
            lab.remove_self(self)
    
    def resizeEvent(self, a0: QResizeEvent) -> None:
        w = self.width()
        # print("Current width", w)
        if w < 1228:
            self.num_cols = 6
        elif 1228 <= w <= 1652:
            self.num_cols = 8
        else:
            self.num_cols = 12
        self.re_render_grid()
        return super().resizeEvent(a0)
    
    def open_existing_spsh_xml(self):
        imgpath = QFileDialog.getOpenFileName(
            caption="Select Spritesheet File",
            filter="PNG Images (*.png)"
        )[0]

        if imgpath != '':
            xmlpath = QFileDialog.getOpenFileName(
                caption="Select XML File",
                filter="XML Files (*.xml)"
            )[0]
            if xmlpath != '':
                trubasenamefn = lambda path: ntpath.basename(path).split('.')[0]
                charname = trubasenamefn(xmlpath)
                if trubasenamefn(imgpath) != trubasenamefn(xmlpath):
                    self.msgbox = QMessageBox(self)
                    self.msgbox.setWindowTitle("Conflicting file names")
                    self.msgbox.setText("The Spritesheet and the XML file have different file names.\nWhich one would you like to use for the character?")
                    self.msgbox.setIcon(QMessageBox.Warning)
                    self.msgbox.addButton("Use XML filename", QMessageBox.YesRole)
                    usespsh = self.msgbox.addButton("Use Spritesheet filename", QMessageBox.NoRole)
                    x = self.msgbox.exec_()
                    clickedbtn = self.msgbox.clickedButton()
                    charname = trubasenamefn(imgpath) if clickedbtn == usespsh else trubasenamefn(xmlpath)
                    print("[DEBUG] Exit status of msgbox: "+str(x))


                update_prog_bar, progbar = display_progress_bar(self, "Extracting sprite frames....")
                QApplication.processEvents()

                sprites = xmlpngengine.split_spsh(imgpath, xmlpath, update_prog_bar)
                for i, (spimg, posename) in enumerate(sprites):
                    self.add_img(imgpath, spimg, posename)
                    update_prog_bar(50 + ((i+1)*50//len(sprites)), imgpath)
                progbar.close()
                
                self.posename_btn.setDisabled(self.num_labels <= 0)
                
                self.charname_textbox.setText(charname)

        
    
    def open_file_dialog(self):
        imgpaths = QFileDialog.getOpenFileNames(
            caption="Select sprite frames", 
            filter="PNG Images (*.png)",
        )[0]

        if imgpaths:
            update_prog_bar, progbar = display_progress_bar(self, "Importing sprite frames....", 0, len(imgpaths))
            QApplication.processEvents()

            for i, pth in enumerate(imgpaths):
                self.add_img(pth)
                update_prog_bar(i+1, pth)
            progbar.close()
        
        if len(self.labels) > 0:
            self.posename_btn.setDisabled(False)
    
    def add_img(self, imgpath, imdat=None, posename=""):
        print("Adding image, prevcount: ", self.num_labels)
        self.num_rows = 1 + self.num_labels//self.num_cols
        
        self.frames_layout.setRowMinimumHeight(self.num_rows - 1, 0)
        self.frames_layout.setRowStretch(self.num_rows - 1, 0)
        
        vspcr = QSpacerItem(1, 1)
        self.frames_layout.addItem(vspcr, self.num_rows, 0, 1, 4)

        hspcr = QSpacerItem(1, 1)
        self.frames_layout.addItem(hspcr, 0, self.num_cols, self.num_rows, 1)
        
        self.labels.append(SpriteFrame(imgpath, self, imdat, posename))
        self.frames_layout.removeWidget(self.add_img_button)
        self.frames_layout.addWidget(self.labels[-1], self.num_labels // self.num_cols, self.num_labels % self.num_cols, Qt.AlignmentFlag(0x1|0x20))
        self.num_labels += 1
        self.frames_layout.addWidget(self.add_img_button, self.num_labels // self.num_cols, self.num_labels % self.num_cols, Qt.AlignmentFlag(0x1|0x20))
    
    def re_render_grid(self):
        self.num_rows = 1 + self.num_labels//self.num_cols
        for i in range(self.num_cols):
            self.frames_layout.setColumnMinimumWidth(i, 0)
            self.frames_layout.setColumnStretch(i, 0)
        for i in range(self.num_rows):
            self.frames_layout.setRowMinimumHeight(i, 0)
            self.frames_layout.setRowStretch(i, 0)

        vspcr = QSpacerItem(1, 1)
        self.frames_layout.addItem(vspcr, self.num_rows, 0, 1, 4)

        hspcr = QSpacerItem(1, 1)
        self.frames_layout.addItem(hspcr, 0, self.num_cols, self.num_rows, 1)
        
        for i, sp in enumerate(self.labels):
            self.frames_layout.addWidget(sp, i//self.num_cols, i%self.num_cols, Qt.AlignmentFlag(0x1|0x20))
        self.frames_layout.removeWidget(self.add_img_button)
        self.frames_layout.addWidget(self.add_img_button, self.num_labels // self.num_cols, self.num_labels % self.num_cols, Qt.AlignmentFlag(0x1|0x20))
    
    def generate_xml(self):
        charname:str = self.charname_textbox.text()
        charname = charname.strip()
        clip = False # self.cliptobbox_check.checkState()
        if self.num_labels > 0 and charname != '':
            savedir = QFileDialog.getExistingDirectory(caption="Save files to...")
            print("Stuff saved to: ", savedir)
            if savedir != '':
                update_prog_bar, progbar = display_progress_bar(self, "Generating....", 0, len(self.labels))
                QApplication.processEvents()

                statuscode, errmsg = xmlpngengine.make_png_xml(
                    [(lab.imgpath, lab.from_single_png, lab.imdat) for lab in self.labels], 
                    [lab.pose_name for lab in self.labels], 
                    savedir, 
                    charname, 
                    False if clip == 0 else True,
                    update_prog_bar,
                    framedat=[
                        {
                            "frameX": lab.framex, 
                            "frameY": lab.framey, 
                            "frameWidth": lab.framew, 
                            "frameHeight": lab.frameh
                        } for lab in self.labels]
                )
                progbar.close()
                if errmsg is None:
                    self.display_msg_box(
                        window_title="Done!", 
                        text="Your files have been generated!\nCheck the folder you had selected",
                        icon=QMessageBox.Information
                    )
                else:
                    self.display_msg_box(
                        window_title="Error!",
                        text=("Some error occured! Error message: " + errmsg),
                        icon=QMessageBox.Critical
                    )
        else:
            errtxt = "Please enter some frames" if self.num_labels <= 0 else "Please enter the name of your character"
            self.display_msg_box(
                window_title="Error!", 
                text=errtxt,
                icon=QMessageBox.Critical
            )
    
    def zoomInPixmap(self):
        if self.icongrid_path and self.icongrid_zoom <= 5:
            self.icongrid_zoom *= 1.1
            icongrid_pixmap = QPixmap(self.icongrid_path)
            w = icongrid_pixmap.width()
            h = icongrid_pixmap.height()
            icongrid_pixmap = icongrid_pixmap.scaled(int(w*self.icongrid_zoom), int(h*self.icongrid_zoom), 1)
            self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.icongrid_holder_label.setPixmap(icongrid_pixmap)
            self.zoom_label.setText("Zoom: %.2f %%" % (self.icongrid_zoom*100))


    def zoomOutPixmap(self):
        if self.icongrid_path and self.icongrid_zoom >= 0.125:
            self.icongrid_zoom /= 1.1
            icongrid_pixmap = QPixmap(self.icongrid_path)
            w = icongrid_pixmap.width()
            h = icongrid_pixmap.height()
            icongrid_pixmap = icongrid_pixmap.scaled(int(w*self.icongrid_zoom), int(h*self.icongrid_zoom), 1)
            self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.icongrid_holder_label.setPixmap(icongrid_pixmap)
            self.zoom_label.setText("Zoom: %.2f %%" % (self.icongrid_zoom*100))
    
    def uploadIconGrid(self):
        print("Uploading icongrid...")
        self.icongrid_path = QFileDialog.getOpenFileName(
            caption="Select the Icon-grid", 
            filter="PNG Images (*.png)",
        )[0]
        icongrid_pixmap = QPixmap(self.icongrid_path)
        self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
        self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
        self.icongrid_holder_label.setPixmap(icongrid_pixmap)
    
    def getNewIconGrid(self):
        if self.icongrid_path != '' and len(self.iconpaths) > 0:
            print("Valid!")
            # savedir = QFileDialog.getExistingDirectory(caption="Save New Icongrid to...")
            # if savedir != '':
            stat, newinds, problemimg, exception_msg = xmlpngengine.appendIconToIconGrid(self.icongrid_path, self.iconpaths) #, savedir)
            print("[DEBUG] Function finished with status: ", stat)
            errmsgs = [
                'Icon grid was too full to insert a new icon', 
                'Your character icon: {} is too big! Max size: 150 x 150',
                'Unable to find suitable location to insert your icon'
            ]

            if exception_msg is not None:
                self.display_msg_box(
                    window_title="An Error occured", 
                    text=("An Exception (Error) oeccured somewhere\nError message:"+exception_msg),
                    icon=QMessageBox.Critical
                )

            if stat == 0:
                self.display_msg_box(
                    window_title="Done!", 
                    text="Your icon-grid has been generated!\nYour icon's indices are {}".format(newinds),
                    icon=QMessageBox.Information
                )
            elif stat == 4:
                self.display_msg_box(
                    window_title="Warning!", 
                    text="One of your icons was smaller than the 150 x 150 icon size!\nHowever, your icon-grid is generated but the icon has been re-adjusted. \nYour icon's indices: {}".format(newinds),
                    icon=QMessageBox.Warning
                )
            else:
                self.display_msg_box(
                    window_title="Error!", 
                    text=errmsgs[stat - 1].format(problemimg),
                    icon=QMessageBox.Critical
                )
            icongrid_pixmap = QPixmap(self.icongrid_path)
            self.icongrid_holder_label.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.scrollAreaWidgetContents_2.setFixedSize(icongrid_pixmap.width(), icongrid_pixmap.height())
            self.icongrid_holder_label.setPixmap(icongrid_pixmap)
        else:
            errtxt = "Please add an icon-grid image" if self.icongrid_path == '' else "Please add an icon"
            self.display_msg_box(
                window_title="Error!", 
                text=errtxt,
                icon=QMessageBox.Critical
            )
    
    def appendIcon(self):
        print("Appending icon")
        self.iconpaths = QFileDialog.getOpenFileNames(
            caption="Select your character icon", 
            filter="PNG Images (*.png)",
        )[0]
        print("Got icon: ", self.iconpaths)
        if len(self.iconpaths) > 0:
            print("Valid selected")
            self.iconselected_label.setText("Number of\nicons selected:\n{}".format(len(self.iconpaths)))
    
    def setAnimationNames(self):
        if len(self.selected_labels) == 0:
            self.display_msg_box(window_title="Error", text="Please select some frames to rename by checking the checkboxes on them", icon=QMessageBox.Critical)
        else:
            text, okPressed = QInputDialog.getText(None, "Change Animation (Pose) Prefix Name", "Current Animation (Pose) prefix:"+(" "*50), QLineEdit.Normal) # very hack-y soln but it works!
            if okPressed and text != '':
                print("new pose prefix = ", text)
                for label in self.selected_labels:
                    label.pose_name = text
                    label.img_label.setToolTip(label.get_tooltip_string(self))
                
                for label in list(self.selected_labels):
                    label.select_checkbox.setChecked(False)
            else:
                print("Cancel pressed!")
    
    def display_msg_box(self, window_title="MessageBox", text="Text Here", icon=None):
        self.msgbox = QMessageBox(self)
        self.msgbox.setWindowTitle(window_title)
        self.msgbox.setText(text)
        if not icon:
            self.msgbox.setIcon(QMessageBox.Information)
        else:
            self.msgbox.setIcon(icon)
        x = self.msgbox.exec_()
        print("[DEBUG] Exit status of msgbox: "+str(x))




if __name__ == '__main__':
    app = QApplication(sys.argv)

    myapp = MyApp()
    myapp.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        print("Closing...")