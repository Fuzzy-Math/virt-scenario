# aginies@suse.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
python GTK3 interface for virt-scenario
"""

import os
import yaml
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, Gdk

import virtscenario.qemulist as qemulist
import virtscenario.hypervisors as hv
import virtscenario.util as util
import virtscenario.configuration as configuration
import virtscenario.scenario as scenario
import virtscenario.host as host
import virtscenario.configstore as configstore
import mygtk.gtkhelper as gtk

# DEBUG
from pprint import pprint

class MyWizard(Gtk.Assistant):

    class MyFilter():
        """
        create a filter for filechooser
        """
        def create_filter(name, list_ext):
            filter = Gtk.FileFilter()
            filter.set_name(name+" Files")
            for ext in list_ext:
                filter.add_pattern("*."+ext)
            return filter

    def start_vm(self, widget):
        """
        use virt-scenario-launch to start the VM
        """
        import subprocess
        win_launch = Gtk.Window(title="Start VM log")
        win_launch.set_default_size(550, 500)
        win_launch.set_resizable(True)

        # Create a box to hold the scrolled window.
        box_launch = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        win_launch.add(box_launch)
        scrolled_window_vm = gtk.GtkHelper.create_scrolled()

        self.textview_vm = Gtk.TextView()
        self.textview_vm.set_editable(False)
        self.textview_vm.set_cursor_visible(False)

        # Add the textview widget to the scrolled window.
        scrolled_window_vm.add(self.textview_vm)
        box_launch.pack_start(scrolled_window_vm, True, True, 0)

        if util.cmd_exists("virt-scenario-launch") is False:
            text_error = "<b>virt-scenario-launch</b> is not available on this system"
            self.dialog_error(text_error)
            return

        buffer_vm = self.textview_vm.get_buffer()

        try:
            out, errs = util.system_command(self.howto)
            buffer_vm.set_text(out)
            end_iter = buffer_vm.get_end_iter()
            self.textview_vm.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)

        except subprocess.CalledProcessError as e:
            # If the command fails, display an error message in the textview widget.
            buffer_vm.set_text(f"Command failed with exit code {e.returncode}: {e.cmd}")
            end_iter = buffer_vm.get_end_iter()
            self.textview_vm.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)

        win_launch.show_all()
        #win_launch.destroy()

    def show_yaml_config(self, widget, whichfile):
        """
        show the YAML file
        """

        def on_delete_event(widget, event):
            widget.destroy()
            return True

        yamlconf = ""
        if whichfile == "vs":
            yamlconf = self.vfilechooser_conf.get_filename()
            print("Show virt-scenario config:"+yamlconf)
        elif whichfile == "hv":
            yamlconf = self.hfilechooser_conf.get_filename()
            print("Show hypervisor config: "+yamlconf)
        if os.path.isfile(yamlconf) is False:
            text_error = "Yaml file not found ("+yamlconf+")"
            self.dialog_error(text_error)
            return

        with open(yamlconf, 'r') as f:
            config = yaml.safe_load(f)

        # Create a Gtk window and a vertical box to hold the frames
        window = Gtk.Window(title="virtscenario configuration")
        window.set_default_size(500, 400)
        window.set_resizable(True)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scrolled = gtk.GtkHelper.create_scrolled()
        scrolled.add_with_viewport(box)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        window.add(scrolled)

        for item, value in config.items():
            grid = Gtk.Grid(column_spacing=12, row_spacing=6)
            frame = gtk.GtkHelper.create_frame(item)
            box.pack_start(frame, False, False, 0)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

            # grid row is 0
            row = 0
            for key in value:
                if isinstance(key, dict):
                    for k, v in key.items():
                        print(str(k)+" "+str(v))
                        label = gtk.GtkHelper.create_label(k, Gtk.Align.END)
                        entry = gtk.GtkHelper.create_entry(v, Gtk.Align.START)
                        grid.attach(label, 0, row, 1, 1)
                        grid.attach(entry, 1, row, 1, 1)
                        row +=1

            print(item)
            if isinstance(value, dict):
                row = 0
                for k in value.keys():
                    print(k)
                    label = gtk.GtkHelper.create_label(k, Gtk.Align.END)
                    grid.attach(label, 0, row, 1, 1)
                    row += 1
                row = 0
                for v in value.values():
                    print(v)
                    entry = gtk.GtkHelper.create_entry(v, Gtk.Align.START)
                    grid.attach(entry, 1, row, 1, 1)
                    row += 1

            frame.add(vbox)
            vbox.pack_start(grid, False, False, 0)

        window.show_all()
        window.connect("delete_event", on_delete_event)

    def __init__(self, conf):

        Gtk.Assistant.__init__(self)
        self.set_title("virt-scenario")
        self.set_default_size(700, 500)
        self.items_scenario = ["Desktop", "Computation", "Secure VM"]
        # set selected scenario to none by default
        self.selected_scenario = None
        # default all expert page not displayed
        self.expert = "off"
        self.force_sev = "off"
        self.howto = self.xml_show_config = ""
        self.overwrite = "off"
        self.conf = conf

        xml_all = None
        if configuration.Configuration.check_conffile(self) is not False:
            configuration.Configuration.basic_config(self)

        self.conffile = conf.conffile #configuration.find_conffile()
        self.hvfile = conf.hvfile # configuration.find_hvfile()

        self.dataprompt = conf.dataprompt
        self.listosdef = conf.listosdef
        self.mode = conf.mode
        self.vm_config_store = self.conf.vm_config_store
        self.vm_list = os.listdir(self.vm_config_store)

        self.hypervisor = hv.select_hypervisor()
        if not self.hypervisor.is_connected():
           print("No connection to LibVirt")
           return
        else:
            self.items_vnet = self.hypervisor.network_list()

        # Connect signals
        self.connect("cancel", Gtk.main_quit)
        self.connect("close", Gtk.main_quit)
        self.connect("prepare", self.on_prepare)
        self.connect("apply", self.on_apply)

    def apply_user_data_on_scenario(self):
        # Now use the wizard data to overwrite some vars
        self.conf.overwrite = self.overwrite
        self.conf.force_sev = self.force_sev
        self.conffile = self.vfilechooser_conf.get_filename()
        self.conf.hvfile = self.hfilechooser_conf.get_filename()

        # VM definition
        self.conf.callsign = self.entry_name.get_text()
        # Get Name
        self.conf.dataprompt.update({'name': self.conf.callsign})
        # Get VCPU
        self.conf.dataprompt.update({'vcpu': int(self.spinbutton_vcpu.get_value())})
        # Get MEMORY
        self.conf.dataprompt.update({'memory': int(self.spinbutton_mem.get_value())})
        # Get bootdev
        tree_iter_bootdev = self.combobox_bootdev.get_active_iter()
        model_bootdev = self.combobox_bootdev.get_model()
        selected_boot_dev_item = model_bootdev[tree_iter_bootdev][0]
        self.conf.dataprompt.update({'boot_dev': selected_boot_dev_item})
        # Get machine type
        tree_iter_machinet = self.combobox_machinet.get_active_iter()
        model_machinet = self.combobox_machinet.get_model()
        selected_machinet = model_machinet[tree_iter_machinet][0]
        self.conf.dataprompt.update({'machine': selected_machinet})
        # Get vnet
        tree_iter_vnet = self.combobox_vnet.get_active_iter()
        model_vnet = self.combobox_vnet.get_model()
        selected_vnet = model_vnet[tree_iter_vnet][0]
        self.conf.dataprompt.update({'vnet': selected_vnet})
        # Get vmimage
        if self.filechooser_vmimage.get_filename() is not None:
            self.conf.dataprompt.update({'vmimage': self.filechooser_vmimage.get_filename()})
        # Get CD/DVD
        if self.filechooser_cd.get_filename() is not None:
            self.conf.dataprompt.update({'dvd': self.filechooser_cd.get_filename()})
            # self.conf.listosdef.update({'boot_dev': "cdrom"})

        #print("DEBUG DEBUG -------------------------------------------------------")
        #pprint(vars(self.conf))
        #print("END DEBUG DEBUG -----------------------------------------------")

    def on_apply(self, current_page):
        """
        Apply all user setting to config and do XML config and Host preparation
        """
        self.apply_user_data_on_scenario()

        # launch the correct scenario
        if self.selected_scenario is not None:
            if self.selected_scenario == "securevm":
                scenario.Scenarios.do_securevm(self, False)
            elif self.selected_scenario == "desktop":
                scenario.Scenarios.do_desktop(self, False)
            elif self.selected_scenario == "computation":
                scenario.Scenarios.do_computation(self, False)
            else:
                print("Unknow selected Scenario!")
        if self.nothing_to_report is False:
            self.show_to_report(self.toreport)

    def show_to_report(self, toreport):

        window = Gtk.Window(title="Warning")
        window.set_default_size(500, 400)
        window.set_resizable(True)
        grid = Gtk.Grid(column_spacing=12, row_spacing=6)

        label_title = gtk.GtkHelper.create_label("Comparison table between user and recommended settings", Gtk.Align.START)
        label_warning = gtk.GtkHelper.create_label("You are over writing scenario setting!", Gtk.Align.START)
        label_warning.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("red"))
        label_warning.modify_font(Pango.FontDescription("Sans Bold 18"))
        label_info = gtk.GtkHelper.create_label("Overwrite are from file: "+self.conffile+"\n", Gtk.Align.START)

        self.liststore = Gtk.ListStore(str, str, str)
        total = len(toreport)+1
        for number in range(1, int(total)):
            self.liststore.append([toreport[number]["title"], toreport[number]["rec"], str(toreport[number]["set"])])

        treeview = Gtk.TreeView(model=self.liststore)
        treeview.get_selection().set_mode(Gtk.SelectionMode.NONE)

        renderer_parameter = Gtk.CellRendererText()
        renderer_parameter.set_property("editable", False)
        renderer_parameter.set_property("weight", Pango.Weight.BOLD)
        column_parameter = Gtk.TreeViewColumn("Parameter", renderer_parameter, text=0)
        treeview.append_column(column_parameter)

        renderer_recommended = Gtk.CellRendererText()
        renderer_recommended.set_property("editable", False)
        renderer_recommended.set_property("alignment", Pango.Alignment.CENTER)
        column_recommended = Gtk.TreeViewColumn("Recommended", renderer_recommended, text=1)
        treeview.append_column(column_recommended)
        recommended_color = Gdk.RGBA()
        recommended_color.parse("#00FF00")  # green
        renderer_recommended.set_property("foreground-rgba", recommended_color)

        renderer_user = Gtk.CellRendererText()
        renderer_user.set_property("editable", False)
        renderer_user.set_property("alignment", Pango.Alignment.CENTER)
        column_user = Gtk.TreeViewColumn("User Settings", renderer_user, text=2)
        treeview.append_column(column_user)
        user_color = Gdk.RGBA()
        user_color.parse("#FF0000")  # Red
        renderer_user.set_property("foreground-rgba", user_color)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(treeview)

        grid.attach(label_title, 0, 0, 1, 1)
        grid.attach(label_warning, 0, 1, 1, 1)
        grid.attach(label_info, 0, 3, 1, 1)
        grid.attach(scrolled_window, 0, 5, 1, 1)
        window.add(grid)
        window.show_all()

    def on_prepare(self, current_page, page):
        """
        remove some unwated pages in case of unneeded
        """
        print("Show page:", self.get_current_page())
        print("Expert mode: "+self.expert)
        print("Force SEV mode: "+self.force_sev)
        print("found: "+str(self.get_n_pages())+ " pages")

        # remove virt scenario config and hypervisor if not expert mode
        if page == self.get_nth_page(1) and self.expert == "off":
            # skip virtscenario page
            self.set_page_complete(current_page, True)
            self.next_page()
            # skip hypervisor page
            self.set_page_complete(current_page, True)
            self.next_page()
            self.commit()

        # after the configuration page check previous config file
        if page > self.get_nth_page(3) and self.overwrite == "off":
            if self.entry_name.get_text() in self.vm_list:
                self.conf.callsign = self.entry_name.get_text()
                tocheck = self.vm_config_store+"/"+self.conf.callsign
                self.userpathincaseof = os.path.expanduser(tocheck)
                print("Error! previous config found")
                text_mdialog = "A configuration for VM: \""+self.conf.callsign+"\" already exist in the directory:\n\""+self.userpathincaseof+"\"\nPlease change the name of the VM \nor use the <b>overwrite</b> option."
                self.dialog_error(text_mdialog)
                # force page 3
                self.set_current_page(3)

        # after scenario selection
        if page > self.get_nth_page(4):
            if self.selected_scenario != "securevm":
                if page == self.get_nth_page(5):
                    self.set_page_complete(current_page, True)
                    self.next_page()
                else:
                    print("Force SEV page available")

        if page >= self.get_nth_page(6):
            if os.path.isfile(self.filename):
                self.xml_show_config = self.show_data_from_xml()
                self.textbuffer_xml.set_text(self.xml_show_config)
                util.to_report(self.toreport, self.conf.conffile)

        if page > self.get_nth_page(5):
            self.howto = "virt-scenario-launch --start "+(self.conf.callsign)
            self.textbuffer_cmd.set_text(self.howto)

    def show_data_from_xml(self):
        """
        show xml data
        """
        with open(self.filename, 'r') as file:
            dump = file.read().rstrip()
        return dump

    def dialog_error(self, message):
    # PAGE Error
        self.mdialog = Gtk.MessageDialog(parent=self.get_toplevel(),
                                         flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                         buttons=Gtk.ButtonsType.OK,
                                         type=Gtk.MessageType.ERROR)

        self.mdialog.set_transient_for(self)
        self.mdialog.set_title("Warning!")
        self.mdialog.set_markup(message)

        def on_response(dialog, response_id):
            dialog.destroy()

        self.mdialog.connect("response", on_response)
        self.mdialog.show()

    def page_intro(self):
    # PAGE Intro
        print("Page Intro")
        box_intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        grid_intro = Gtk.Grid(column_spacing=12, row_spacing=6)
        box_intro.pack_start(grid_intro, False, False, 0)

        label_title = Gtk.Label(label="virt-scenario")
        label_title.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("green"))
        label_title.modify_font(Pango.FontDescription("Sans Bold 24"))
        label_intro = Gtk.Label()
        text_intro = "\nPrepare a <b>libvirt XML</b> guest and host configuration to"
        text_intro += " run a customized guest.\n"
        text_intro += "\nCustomization to match a specific scenario is not graved"
        text_intro += " in stone. The idea is to prepare a configuration which should"
        text_intro += " improved the usage compared to a basic setting.\n"
        text_intro += "\nThis will <b>NOT guarantee</b> anything."
        label_intro.set_markup(text_intro)
        label_intro.set_line_wrap(True)
        label_warning = gtk.GtkHelper.create_label("(Warning: still under devel ...)", Gtk.Align.START)
        label_warning.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("red"))
        label_warning.modify_font(Pango.FontDescription("Sans Bold 12"))
        url = Gtk.LinkButton.new_with_label(uri="https://www.github.com/aginies/virt-scenario",label="virt-scenario Homepage")
        url.set_halign(Gtk.Align.START)

        grid_a = Gtk.Grid(column_spacing=12, row_spacing=6)
        frame_a = gtk.GtkHelper.create_frame("Expert")
        vbox_a = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        label_expert = gtk.GtkHelper.create_label("Expert Mode", Gtk.Align.END)
        gtk.GtkHelper.margin_top_bottom_left(label_expert)
        switch_expert = Gtk.Switch()
        gtk.GtkHelper.margin_top_left(switch_expert)
        switch_expert.set_margin_bottom(18)
        switch_expert.set_tooltip_text("Add some pages with expert configuration.\n(You can choose configurations files and set storage options)")
        switch_expert.connect("notify::active", self.on_switch_expert_activated)
        switch_expert.set_active(False)
        switch_expert.set_halign(Gtk.Align.START)

        grid_a.attach(label_expert, 0, 0, 1, 1)
        grid_a.attach(switch_expert, 1, 0, 1, 1)
        vbox_a.pack_start(grid_a, False, False, 0)
        frame_a.add(vbox_a)
        box_intro.pack_start(frame_a, False, False, 0)

        grid_intro.attach(label_title, 0, 0, 1, 1)
        grid_intro.attach(label_warning, 0, 1, 1, 1)
        grid_intro.attach(label_intro, 0, 2, 4, 4)
        grid_intro.attach(url, 0, 6, 1, 1)

        self.append_page(box_intro)
        self.set_page_type(box_intro, Gtk.AssistantPageType.INTRO)
        self.set_page_complete(box_intro, True)

    def page_virtscenario(self):
        # PAGE: virt scenario
        print("Page virtscenario")
        box_vscenario = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append_page(box_vscenario)
        self.set_page_type(box_vscenario, Gtk.AssistantPageType.CONTENT)
        frame_vconf = gtk.GtkHelper.create_frame("Virtscenario configuration")

        # Create a grid layout for virt-scenario configuration file
        grid_vconf = Gtk.Grid(column_spacing=12, row_spacing=6)
        frame_vconf.add(grid_vconf)
        box_vscenario.pack_start(frame_vconf, False, False, 0)
        label_vconf = gtk.GtkHelper.create_label("virt-scenario Configuration file", Gtk.Align.END)
        gtk.GtkHelper.margin_top_left(label_vconf)
        self.vfilechooser_conf = Gtk.FileChooserButton(title="Select virt-scenario Configuration File")
        self.vfilechooser_conf.set_filename(self.conffile)
        self.vfilechooser_conf.set_halign(Gtk.Align.START)
        gtk.GtkHelper.margin_top_left(self.vfilechooser_conf)
        yaml_f = self.MyFilter.create_filter("yaml/yml", ["yaml", "yml"])
        self.vfilechooser_conf.add_filter(yaml_f)
        button_vshow = Gtk.Button(label="Show configuration")
        gtk.GtkHelper.margin_bottom_left(button_vshow)
        button_vshow.connect("clicked", lambda widget: self.show_yaml_config(button_vshow, "vs"))

        grid_vconf.attach(label_vconf, 0, 0, 1, 1)
        grid_vconf.attach(self.vfilechooser_conf, 1, 0, 1, 1)
        grid_vconf.attach(button_vshow, 1, 1, 1, 1)

        self.set_page_complete(box_vscenario, True)

    def page_hypervisors(self):
        # PAGE: hypervisor 
        print("Page hypervisor")
        box_hyper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append_page(box_hyper)
        self.set_page_type(box_hyper, Gtk.AssistantPageType.CONTENT)
        frame_hconf = gtk.GtkHelper.create_frame("Hypervisor configuration")

        grid_conf = Gtk.Grid(column_spacing=12, row_spacing=6)
        frame_hconf.add(grid_conf)
        box_hyper.pack_start(frame_hconf, False, False, 0)
        label_hconf = gtk.GtkHelper.create_label("Hypervisor Configuration file", Gtk.Align.END)
        gtk.GtkHelper.margin_top_left(label_hconf)
        self.hfilechooser_conf = Gtk.FileChooserButton(title="Select Hypervisor Configuration File")
        self.hfilechooser_conf.set_filename(self.hvfile)
        self.hfilechooser_conf.set_halign(Gtk.Align.START)
        gtk.GtkHelper.margin_top_left(self.hfilechooser_conf)
        yaml_f = self.MyFilter.create_filter("yaml/yml", ["yaml", "yml"])
        self.hfilechooser_conf.add_filter(yaml_f)
        button_show = Gtk.Button(label="Show configuration")
        button_show.connect("clicked", lambda widget: self.show_yaml_config(button_show, "hv"))
        gtk.GtkHelper.margin_bottom_left(button_show)

        grid_conf.attach(label_hconf, 0, 0, 1, 1)
        grid_conf.attach(self.hfilechooser_conf, 1, 0, 1, 1)
        grid_conf.attach(button_show, 1, 1, 1, 1)

        self.set_page_complete(box_hyper, True)

    def page_scenario(self):
        # PAGE: scenario
        print("Page Scenario")
        self.main_scenario = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append_page(self.main_scenario)
        self.set_page_title(self.main_scenario, "Scenario Selection")
        self.set_page_type(self.main_scenario, Gtk.AssistantPageType.CONTENT)

        frame_scena = gtk.GtkHelper.create_frame("Scenario")
        grid_scena = Gtk.Grid(column_spacing=12, row_spacing=6)

        urltoinfo = Gtk.LinkButton.new_with_label(
            uri="https://github.com/aginies/virt-scenario#default-settings-comparison",
            label="Scenarios Documentation Comparison"
        )
        urltoinfo.set_margin_left(18)
        urltoinfo.set_margin_top(18)
        frame_scena.add(grid_scena)
        self.main_scenario.pack_start(frame_scena, False, False, 0)

        label_scenario = gtk.GtkHelper.create_label("Select Scenario", Gtk.Align.END)
        self.scenario_combobox = Gtk.ComboBoxText()
        self.scenario_combobox.set_tooltip_text("Will preload an optimized VM configration")
        self.scenario_combobox.set_entry_text_column(0)

        # Add some items to the combo box
        for item in self.items_scenario:
            self.scenario_combobox.append_text(item)
        # dont select anything by default
        self.scenario_combobox.set_active(-1)

        grid_scena.attach(urltoinfo, 0, 0, 2, 1)
        grid_scena.attach(label_scenario, 0, 2, 1, 1)
        grid_scena.attach(self.scenario_combobox, 1 , 2, 1, 1)

        #Create a horizontal box for overwrite config option

        label_overwrite = gtk.GtkHelper.create_label("Overwrite Previous Config", Gtk.Align.END)
        gtk.GtkHelper.margin_bottom_left(label_overwrite)
        switch_overwrite = Gtk.Switch()
        switch_overwrite.set_margin_bottom(18)
        switch_overwrite.set_halign(Gtk.Align.START)
        switch_overwrite.connect("notify::active", self.on_switch_overwrite_activated)
        switch_overwrite.set_tooltip_text("This will overwrite any previous VM configuration!")
        switch_overwrite.set_active(False)
        grid_scena.attach(label_overwrite, 0, 3, 1, 1)
        grid_scena.attach(switch_overwrite, 1, 3, 1, 1)

        # Handle scenario selection
        self.scenario_combobox.connect("changed", self.on_scenario_changed)
        if self.scenario_combobox.get_active() != -1:
            self.set_page_complete(self.main_scenario, True)

    def page_storage(self):
        # PAGE storage
# disk_type: file
# disk cache: writeback, writethrough, none, unsafe, directsync
# disk_target: vda
# disk_bus: virtio
# path: /var/lib/libvirt/images
# format: qcow2, raw
# host side: qemu-img creation options (-o), qemu-img --help
# capacity: 20
# cluster_size: 1024k
# lazy_refcounts: on
# preallocation: off, metadata (qcow2), falloc, full
# compression_type: zlib
# encryption: on, off

        print("Page storage")
        # Create a vertical box to hold the file selection button and the entry box
        self.main_svbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        #self.append_page(self.main_svbox)
        #self.set_page_title(main_svbox, "Storage")
        self.set_page_type(self.main_svbox, Gtk.AssistantPageType.CONTENT)
        self.set_page_complete(self.main_svbox, True)

        frame_scfg = gtk.GtkHelper.create_frame("Storage Configuration")
        vbox_scfg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        grid_sto = Gtk.Grid(column_spacing=12, row_spacing=6)
        label_spinbutton_capacity = gtk.GtkHelper.create_label("Capacity (GiB)", Gtk.Align.END)
        self.spinbutton_capacity = Gtk.SpinButton()
        self.spinbutton_capacity.set_range(1, 32)
        self.spinbutton_capacity.set_increments(1, 1)

        label_spinbutton_cluster = gtk.GtkHelper.create_label("Cluster Size in KiB", Gtk.Align.END)
        label_spinbutton_cluster.set_margin_left(18)
        self.spinbutton_cluster = Gtk.SpinButton()
        self.spinbutton_cluster.set_range(1, 2048)
        self.spinbutton_cluster.set_increments(16, 1)

        label_disk_cache = gtk.GtkHelper.create_label("Disk Cache", Gtk.Align.END)
        self.combobox_disk_cache = Gtk.ComboBoxText()
        self.combobox_disk_cache.set_entry_text_column(0)

        items_disk_cache = qemulist.DISK_CACHE
        for item in items_disk_cache:
            self.combobox_disk_cache.append_text(item)
        # TOFIX
        self.combobox_disk_cache.set_active(0)

        # Handle disk cache change
        #self.combobox_bootdev.connect("changed", self.on_disk_cache_changed)

        label_disk_target = gtk.GtkHelper.create_label("Disk Target", Gtk.Align.END)
        label_disk_target.set_margin_top(18)
        self.combobox_disk_target = Gtk.ComboBoxText()
        self.combobox_disk_target.set_margin_top(18)

        items_disk_target = ['vda', 'vdb', 'vdc']
        for item in items_disk_target:
            self.combobox_disk_target.append_text(item)
        self.combobox_disk_target.set_active(0)

        # Handle disk target change
        #self.combobox_disk_target.connect("changed", self.on_disk_target_changed)

        label_prealloc = gtk.GtkHelper.create_label("Pre-allocation", Gtk.Align.END)
        label_prealloc.set_margin_left(18)
        self.combobox_prealloc = Gtk.ComboBoxText()
        self.combobox_prealloc.set_entry_text_column(0)

        items_prealloc = qemulist.PRE_ALLOCATION
        for item in items_prealloc:
            self.combobox_prealloc.append_text(item)
        self.combobox_prealloc.set_active(0)

        label_encryption = gtk.GtkHelper.create_label("Encryption", Gtk.Align.END)
        gtk.GtkHelper.margin_bottom_left(label_encryption)
        self.combobox_encryption = Gtk.ComboBoxText()
        self.combobox_encryption.set_entry_text_column(0)
        self.combobox_encryption.set_margin_bottom(18)

        for item in ['on', 'off']:
            self.combobox_encryption.append_text(item)
        self.combobox_encryption.set_active(1)

        label_lazyref = gtk.GtkHelper.create_label("Lazy Ref Count", Gtk.Align.END)
        label_lazyref.set_margin_left(18)
        self.combobox_lazyref = Gtk.ComboBoxText()
        self.combobox_lazyref.set_entry_text_column(0)

        for item in ['on', 'off']:
            self.combobox_lazyref.append_text(item)
        self.combobox_lazyref.set_active(1)

        grid_sto.attach(label_disk_target, 0, 0, 1, 1)
        grid_sto.attach(self.combobox_disk_target, 1, 0, 1, 1)
        grid_sto.attach(label_spinbutton_capacity, 0, 1, 1, 1)
        grid_sto.attach(self.spinbutton_capacity, 1, 1, 1, 1)
        grid_sto.attach(label_spinbutton_cluster, 0, 2, 1, 1)
        grid_sto.attach(self.spinbutton_cluster, 1, 2, 1, 1)
        grid_sto.attach(label_disk_cache, 0, 3, 1, 1)
        grid_sto.attach(self.combobox_disk_cache, 1, 3, 1, 1)
        grid_sto.attach(label_lazyref, 0, 4, 1, 1)
        grid_sto.attach(self.combobox_lazyref, 1, 4, 1, 1)
        grid_sto.attach(label_prealloc, 0, 5, 1, 1)
        grid_sto.attach(self.combobox_prealloc, 1, 5, 1, 1)
        grid_sto.attach(label_encryption, 0, 6, 1, 1)
        grid_sto.attach(self.combobox_encryption, 1, 6, 1, 1)
 
        vbox_scfg.pack_start(grid_sto, False, False, 0)
        frame_scfg.add(vbox_scfg)
        self.main_svbox.pack_start(frame_scfg, False, False, 0)

    def page_configuration(self):
        # PAGE configuration
        print("Page configuration")
        # Create a vertical box to hold the file selection button and the entry box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append_page(main_vbox)
        self.set_page_title(main_vbox, "Configuration")
        self.set_page_type(main_vbox, Gtk.AssistantPageType.CONFIRM)
        self.set_page_complete(main_vbox, True)

        frame_cfg = gtk.GtkHelper.create_frame("Configuration")
        vbox_cfg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        grid_cfg = Gtk.Grid(column_spacing=12, row_spacing=6)
        label_name = gtk.GtkHelper.create_label("VM Name", Gtk.Align.END)
        gtk.GtkHelper.margin_top_left(label_name)
        self.entry_name = Gtk.Entry()
        self.entry_name.set_text("VMname")
        self.entry_name.set_margin_top(18)

        label_spinbutton_vcpu = gtk.GtkHelper.create_label("Vcpu", Gtk.Align.END)
        self.spinbutton_vcpu = Gtk.SpinButton()
        self.spinbutton_vcpu.set_range(1, 32)
        self.spinbutton_vcpu.set_increments(1, 1)

        label_spinbutton_mem = gtk.GtkHelper.create_label("Memory in GiB", Gtk.Align.END)
        self.spinbutton_mem = Gtk.SpinButton()
        self.spinbutton_mem.set_range(1, 32)
        self.spinbutton_mem.set_increments(1, 1)

        label_bootdev = gtk.GtkHelper.create_label("Bootdev", Gtk.Align.END)
        self.combobox_bootdev = Gtk.ComboBoxText()
        self.combobox_bootdev.set_entry_text_column(0)

        items_bootdev = qemulist.LIST_BOOTDEV
        for item in items_bootdev:
            self.combobox_bootdev.append_text(item)
        self.combobox_bootdev.set_active(0)

        # Handle bootdev selection
        self.combobox_bootdev.connect("changed", self.on_bootdev_changed)

        label_machinet = gtk.GtkHelper.create_label("Machine Type", Gtk.Align.END)
        self.combobox_machinet = Gtk.ComboBoxText()

        items_machinet = qemulist.LIST_MACHINETYPE
        for item in items_machinet:
            self.combobox_machinet.append_text(item)

        # Handle machine type selection
        self.combobox_machinet.connect("changed", self.on_machinet_changed)

        label_vnet = gtk.GtkHelper.create_label("Virtual Network", Gtk.Align.END)
        gtk.GtkHelper.margin_bottom_left(label_vnet)
        self.combobox_vnet = Gtk.ComboBoxText()
        self.combobox_vnet.set_entry_text_column(0)
        self.combobox_vnet.set_margin_bottom(18)

        for item in self.items_vnet:
            self.combobox_vnet.append_text(item)
        self.combobox_vnet.set_active(0)

        grid_cfg.attach(label_name, 0, 0, 1, 1)
        grid_cfg.attach(self.entry_name, 1, 0, 1, 1)
        grid_cfg.attach(label_spinbutton_vcpu, 0, 1, 1, 1)
        grid_cfg.attach(self.spinbutton_vcpu, 1, 1, 1, 1)
        grid_cfg.attach(label_spinbutton_mem, 0, 2, 1, 1)
        grid_cfg.attach(self.spinbutton_mem, 1, 2, 1, 1)
        grid_cfg.attach(label_bootdev, 0, 3, 1, 1)
        grid_cfg.attach(self.combobox_bootdev, 1, 3, 1, 1)
        grid_cfg.attach(label_machinet, 0, 4, 1, 1)
        grid_cfg.attach(self.combobox_machinet, 1, 4, 1, 1)
        grid_cfg.attach(label_vnet, 0, 5, 1, 1)
        grid_cfg.attach(self.combobox_vnet, 1, 5, 1, 1)
        vbox_cfg.pack_start(grid_cfg, False, False, 0)
        frame_cfg.add(vbox_cfg)
        main_vbox.pack_start(frame_cfg, False, False, 0)

        vbox_cfgplus = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame_cfgplus = gtk.GtkHelper.create_frame("Image / CD / DVD")

        grid_cfgplus = Gtk.Grid(column_spacing=12, row_spacing=6)
        label_vmimage = gtk.GtkHelper.create_label("VM Image", Gtk.Align.END)
        gtk.GtkHelper.margin_top_left(label_vmimage)
        self.filechooser_vmimage = Gtk.FileChooserButton(title="Select The VM Image")
        self.filechooser_vmimage.set_margin_top(18)
        image_f = self.MyFilter.create_filter("raw/qcow2", ["raw", "qcow2"])
        self.filechooser_vmimage.add_filter(image_f)

        label_cd = gtk.GtkHelper.create_label("CD/DVD", Gtk.Align.END)
        label_cd.set_margin_bottom(18)
        self.filechooser_cd = Gtk.FileChooserButton(title="Select The CD/DVD Image")
        self.filechooser_cd.set_margin_bottom(18)
        iso_f = self.MyFilter.create_filter("ISO", ["iso"])
        self.filechooser_cd.add_filter(iso_f)

        grid_cfgplus.attach(label_vmimage, 0, 0, 1, 1)
        grid_cfgplus.attach(self.filechooser_vmimage, 1, 0, 1, 1)
        grid_cfgplus.attach(label_cd, 0, 1, 1, 1)
        grid_cfgplus.attach(self.filechooser_cd, 1, 1, 1, 1)
        frame_cfgplus.add(grid_cfgplus)
        main_vbox.pack_start(frame_cfgplus, False, False, 0)

        # Handle vnet selection
        self.combobox_vnet.connect("changed", self.on_vnet_changed)

    def page_end(self):
        # PAGE : End
        print("Page End")
        box_end = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        grid_end = Gtk.Grid(column_spacing=12, row_spacing=6)
        frame_launch = gtk.GtkHelper.create_frame("Launch VM")
        # hbox to store launch info
        hbox_launch = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        label_launch = Gtk.Label()
        label_launch.set_halign(Gtk.Align.START)
        text_start = "Use the <b>virt-scenario-launch</b> tool:"
        label_launch.set_markup(text_start)
        label_launch.set_line_wrap(False)
        hbox_launch.pack_start(label_launch, False, False, 0)
        gtk.GtkHelper.margin_top_left(hbox_launch)

        self.textview_cmd = Gtk.TextView()
        self.textview_cmd.set_editable(False)
        self.textbuffer_cmd = self.textview_cmd.get_buffer()
        hbox_launch.pack_start(self.textview_cmd, False, False, 0)
        gtk.GtkHelper.margin_bottom_left(hbox_launch)

        self.button_start = Gtk.Button(label="Start the Virtual Machine")
        self.button_start.connect("clicked", self.start_vm)
        self.button_start.set_margin_right(18)
        hbox_launch.pack_start(self.button_start, False, False, 0)

        label_vm = Gtk.Label()
        text_end = "(You can also use <b>virt-manager</b>)"
        label_vm.set_markup(text_end)
        gtk.GtkHelper.margin_top_left(label_vm)
        label_vm.set_alignment(0,0)
        #hbox_launch.pack_start(label_vm, False, False, 0)

        # store everything in the frame
        frame_launch.add(hbox_launch)
        grid_end.attach(frame_launch, 0, 0, 1, 1)

        frame_xml = gtk.GtkHelper.create_frame("XML")
        hbox_xml = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        #label_xml = Gtk.Label()
        #label_xml.set_markup("<b>XML</b> configuration generated")
        #label_xml.set_alignment(0,0)
        #hbox_xml.pack_start(label_xml, False, False, 0)

        scrolledwin_xml = gtk.GtkHelper.create_scrolled()
        textview_xml = Gtk.TextView()
        textview_xml.set_editable(False)
        self.textbuffer_xml = textview_xml.get_buffer()
        scrolledwin_xml.add(textview_xml)
        hbox_xml.pack_start(scrolledwin_xml, True, True, 0)
        gtk.GtkHelper.margin_top_left(hbox_xml)
        hbox_xml.set_margin_bottom(18)
        hbox_xml.set_margin_right(18)

        frame_xml.add(hbox_xml)
        grid_end.attach(frame_xml, 0, 1, 1, 1)
        # add the grid to the main box
        box_end.pack_start(grid_end, True, True, 0)

        self.append_page(box_end)
        self.set_page_title(box_end, "HowTo")
        self.set_page_type(box_end, Gtk.AssistantPageType.SUMMARY)
        self.set_page_complete(box_end, True)

    def page_forcesev(self):
        print("Page SEV")
        # force SEV: for secure VM
        box_forcesev = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.append_page(box_forcesev)
        self.set_page_type(box_forcesev, Gtk.AssistantPageType.CONTENT)
        grid_forcesev = Gtk.Grid()
        label_forcesev = gtk.GtkHelper.create_label("Force SEV", Gtk.Align.END)
        switch_forcesev = Gtk.Switch()
        switch_forcesev.connect("notify::active", self.on_switch_forcesev_activated)
        switch_forcesev.set_halign(Gtk.Align.START)
        switch_forcesev.set_active(False)
        grid_forcesev.attach(label_forcesev, 0, 0, 1, 1)
        grid_forcesev.attach(switch_forcesev, 1, 0, 1, 1)
        box_forcesev.pack_start(grid_forcesev, False, False, 0)

        self.set_page_complete(box_forcesev, True)

    def on_scenario_changed(self, combo_box):
        # add the page only if secure VM is selected
        # Get the selected scenario
        tree_iter = combo_box.get_active_iter()
        if tree_iter is not None:
            model = combo_box.get_model()
            selected_item = model[tree_iter][0]
            print("Selected item: {}".format(selected_item))
            # enable the next button now
            self.set_page_complete(self.main_scenario, True)

        if selected_item == "Secure VM":
            print("Secure vm selected")
            self.force_sev = "on"
            self.selected_scenario = "securevm"
            sev_info = scenario.host.sev_info(self.hypervisor)
            if not sev_info.sev_supported:
                util.print_error("Selected hypervisor ({}) does not support SEV".format(self.hypervisor.name))
                self.set_page_complete(self.box_scenario, False)
                text_mdialog = "Selected hypervisor ({}) does not support SEV".format(self.hypervisor.name)
                text_mdialog += "\nPlease select another scenario"
                self.dialog_error(text_mdialog)
                return

            self.conf = scenario.Scenarios.pre_secure_vm(self, "securevm", sev_info)
            self.conf.memory_pin = True
        elif selected_item == "Desktop":
            print("Desktop scenario")
            self.force_sev = "off"
            self.selected_scenario = "desktop"
            self.conf = scenario.Scenarios.pre_desktop(self, "desktop")
            self.conf.memory_pin = False
        elif selected_item == "Computation":
            print("Computation scenario")
            self.force_sev = "off"
            self.selected_scenario = "computation"
            self.conf = scenario.Scenarios.pre_computation(self, "computation")
            self.conf.memory_pin = False

        ## update data with the selected scenario
        self.entry_name.set_text(self.conf.name['VM_name'])
        self.spinbutton_vcpu.set_value(int(self.conf.vcpu['vcpu']))
        self.spinbutton_mem.set_value(int(self.conf.memory['max_memory']))
        ## set machine type
        search_machinet = self.conf.osdef['machine']
        self.search_in_comboboxtext(self.combobox_machinet, search_machinet)
        ## set boot dev
        search_bootdev = self.conf.osdef['boot_dev']
        self.search_in_comboboxtext(self.combobox_bootdev, search_bootdev)
        ## STORAGE
        ## set prealloc
        #search_prealloc = self.STORAGE_DATA_REC['preallocation']
        #self.search_in_comboboxtext(self.combobox_prealloc, search_prealloc)
        ## set encryption
        #search_encryption = self.STORAGE_DATA_REC['encryption']
        #self.search_in_comboboxtext(self.combobox_encryption, search_encryption)
        ## set disk_cache
        #search_disk_cache = self.STORAGE_DATA_REC['disk_cache']
        #self.search_in_comboboxtext(self.combobox_disk_cache, search_disk_cache)
        ## set lazy_ref_count
        #search_lazyref = self.STORAGE_DATA_REC['lazy_refcounts']
        #self.search_in_comboboxtext(self.combobox_lazyref, search_lazyref)
        ## set cluster_size
        #cluster_size = self.STORAGE_DATA['cluster_size']
        #self.spinbutton_cluster.set_value(int(cluster_size))
        ## set capacity
        #capacity = self.STORAGE_DATA['capacity']
        #self.spinbutton_capacity.set_value(int(capacity))
        ## set disk target
        #search_disk_target = self.STORAGE_DATA['disk_target']
        #self.search_in_comboboxtext(self.combobox_disk_target, search_disk_target)

    def search_in_comboboxtext(self, combobox, search_string):
        matching_item = None
        print("Search string: "+search_string)
        for i in range(combobox.get_model().iter_n_children(None)):
            itera = combobox.get_model().iter_nth_child(None, i)
            if combobox.get_model().get_value(itera, 0) == search_string:
                matching_item = itera
                break
        if matching_item is not None:
            combobox.set_active_iter(matching_item)
        else:
            util.print_error("Can not find: "+str(matching_item))

    def on_bootdev_changed(self, combo_box):
        # Get the selected item
        tree_iter = combo_box.get_active_iter()
        if tree_iter is not None:
            model = combo_box.get_model()
            selected_item = model[tree_iter][0]
            print("Selected Boot device: {}".format(selected_item))

    def on_machinet_changed(self, combo_box):
        # Get the selected item
        tree_iter = combo_box.get_active_iter()
        if tree_iter is not None:
            model = combo_box.get_model()
            selected_item = model[tree_iter][0]
            print("Selected machine type: {}".format(selected_item))

    def on_vnet_changed(self, combo_box):
        # Get the selected item
        tree_iter = combo_box.get_active_iter()
        if tree_iter is not None:
            model = combo_box.get_model()
            selected_item = model[tree_iter][0]
            print("Selected Virtual Network: {}".format(selected_item))

    def on_switch_expert_activated(self, switch, gparam):
        if switch.get_active():
            self.expert = "on"
        else:
            self.expert = "off"
        print("Switch Expert was turned", self.expert)

    def on_switch_forcesev_activated(self, switch, gparam):
        if switch.get_active():
            self.force_sev = "on"
        else:
            self.force_sev = "off"
        print("Switch Force SEV was turned", self.force_sev)

    def on_switch_overwrite_activated(self, switch, gparam):
        if switch.get_active():
            self.overwrite = "on"
        else:
            self.overwrite = "off"
        print("Switch Overwrite Config was turned", self.overwrite)

    def on_destroy(self, widget):
        """
        Destroy all win
        """
        Gtk.main_quit()

def main():
    """
    Main GTK
    """
    conf = configuration.Configuration()
    win = MyWizard(conf)
    win.page_intro() # 0
    win.page_virtscenario() # 1
    win.page_hypervisors() # 2
    win.page_scenario() # 3
    #win.page_storage() # 4
    win.page_configuration() # 4
    win.page_forcesev() # 5
    win.page_end() # 6

    win.show_all()
    Gtk.main()
