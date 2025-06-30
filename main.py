#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import curses
from os import listdir, system
import configparser
from textual.app import App, ComposeResult
from textual.widgets import Tree, Log
import shutil

#menu_file = '/etc/xdg/menus/applications-merged/kali-applications.menu'
#tree = ET.parse(menu_file)
#xml_root = tree.getroot()
#menus = [menuname.text for menuname in xml_root[1]]

def get_package_list():
    config = configparser.ConfigParser()
    kali_menu_apps = '/usr/share/kali-menu/applications/'
    categories = {}
    for filename in listdir(kali_menu_apps):
        if filename[:4] == 'kali':
            desktop_file = config.read(kali_menu_apps+filename)
            tool_categories = config['Desktop Entry']['Categories'].split(';')
            tool_categories = list(filter(None, tool_categories))
            for category in tool_categories:
                if category not in categories:
                    categories[category] = []
                categories[category] += [dict(config['Desktop Entry'])]
    return categories

class TreeApp(App):

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree(xml_root[0].text)
        tree.show_root=False
        tree.root.expand()

        packages = get_package_list()

        def walk_xml(branch, xml):                          
            for entity in xml:
                if entity.tag == 'Menu':                                # If we find a menu
                    menu = branch.add(entity[0].text)                   #  add it to the tree
                    walk_xml(menu, entity)                              #  and recurse through it
                elif entity.tag == 'Directory':
                    dirname = entity.text.removesuffix('.directory')        # If we find a directory
                    if packages.get(dirname):                               #  that we saw as a tool category
                        for tool in packages[dirname]:                      #  for each tool in the category
                            if shutil.which(tool['name']):                  #  if it exists on the system
                                menu = branch.add_leaf(tool['name'], data=tool) #  add it to the tree
        walk_xml(tree.root, xml_root)
        yield tree

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        self.selected_node = event.node
        if self.selected_node.data:
            #self.notify(str(self.selected_node.data))
            if self.selected_node.data['terminal'] == 'true':
                with self.suspend():
                    session_name = self.selected_node.data['name']
                    system(f'''tmux new-session -d -s {session_name} ''')
                    system(f'''tmux send-keys -t {session_name} '{self.selected_node.data['exec']}' ''')
                    system(f'''tmux attach -t {session_name}''')

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self.highlighted_node = event.node
        if self.highlighted_node.data:
            self.notify(self.highlighted_node.data['comment'], \
                title=self.highlighted_node.data['name'])

if __name__ == "__main__":
    menu_file = '/etc/xdg/menus/applications-merged/kali-applications.menu'
    tree = ET.parse(menu_file)
    xml_root = tree.getroot()
    menus = [menuname.text for menuname in xml_root[1]]

    app = TreeApp()
    app.run()
