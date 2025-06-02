
class UI:
    def __init__(self, client):
        self.client = client
    
    def draw_line(self, x0, y0, x1, y1, update=True):
        l = f"L{x0} {y0} {x1} {y1}"
        print(l)
        self.client.queue_send(l.encode())
        if update:
            self.commit()
    
    def draw_text(self, x0, y0, text, update=True):
        self.client.queue_send(f"S{x0} {y0} {text}".encode())
        if update:
            self.commit()
    
    def clear(self, update=True):
        self.client.queue_send(b"C")
        if update:
            self.commit()

    def commit(self):
        self.client.queue_send(b"D")

class Menu(UI):
    def update(self, title=None, commands=None):
        if title:
            self.title = title
        
        if commands is not None:
            self.commands = commands

        self.items = [
            self.title,
            "..",
            *(self.commands.keys())
        ]

        if self.selected > len(self.items):
            self.selected = len(self.items)-1

    def __init__(self, client, title, commands={}, parent=None):
        super().__init__(client)
        self.parent = parent
        self.delegate = None

        self.selected = 1
        self.update(title, commands)

        self.line_height = 10
        self.screen_height = 64
        self.screen_width = 128

    def draw(self):
        if self.delegate:
            return self.delegate.draw()

        screen_split = self.screen_height/2
        offset = min(0, -(self.selected*self.line_height-(screen_split-screen_split%self.line_height)))

        self.clear(update=False)
        print(self.items)
        for i in range(len(self.items)):
            if i*self.line_height+offset > self.screen_height or i*self.line_height+offset < 0:
                continue
            self.draw_text(0 if i == 0 else 10, offset+i*10, self.items[i], update=False)
            if i == self.selected:
                y = int(offset+i*self.line_height+self.line_height//2+1)
                self.draw_line(2, y, 8, y, update=False)
        self.commit()
    
    def up(self):
        if self.delegate:
            return self.delegate.up()

        if self.selected > 1:
            self.selected -= 1
        else:
            self.selected = len(self.items)-1
        self.draw()
    
    def down(self):
        if self.delegate:
            return self.delegate.down()

        if self.selected < len(self.items)-1:
            self.selected += 1
        else:
            self.selected = 1
        self.draw()
    
    def is_special_selected(self):
        return self.selected <= 1
    
    def select(self):
        if self.delegate:
            return self.delegate.select()

        if self.selected == 1:
            self.back()
        else:
            command = self.commands[self.items[self.selected]]
            if callable(command):
                result = command()
                if isinstance(result, Menu):
                    self.start_delegating(result)
            elif isinstance(command, Menu):
                print(command)
                self.start_delegating(command)
            else:
                print(f"Don't know how to handle command {self.items[self.selected]} - {command}")
    
    def start_delegating(self, menu: 'Menu'):
        self.delegate = menu
        self.delegate.parent = self
        self.delegate.draw()

    def back(self):
        if self.delegate:
            return self.delegate.back()

        if callable(self.parent):
            self.parent()
        elif isinstance(self.parent, Menu):
            self.parent.stop_delegating()
        else:
            print(f"Don't know how to handle parent {self.parent}")

    def stop_delegating(self):
        self.delegate = None
        self.draw()
    
    def __repr__(self):
        return f"Menu({self.title}, {self.commands.keys()}, {self.parent} - {self.selected})"