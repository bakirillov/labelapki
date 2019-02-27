import os
import sys
import pygame
import argparse
import numpy as np
import pandas as pd
import pickle as pkl
import os.path as op


class App():
    
    def __init__(self, input_folder, output_fn, number):
        pygame.init()
        pygame.display.set_caption("labelapki")
        self.current_image_number = 0
        self.exts = ["jpg", "png"]
        self.action_label = "Started"
        self.clock = pygame.time.Clock()
        self.number = number
        self.font = pygame.font.SysFont("freeserif", 18)
        self.folder = input_folder
        self.output_fn = output_fn
        self.screen = pygame.display.set_mode((1280, 800))
        self.mouse_pressed = []
        self.current_img_boundaries = None
        self.keyboard = {
            pygame.K_SPACE: "Done&Next",
            pygame.K_c: "Clear",
            pygame.K_ESCAPE: "Save",
            pygame.K_0: "Assign 0",
            pygame.K_1: "Assign 1",
            pygame.K_2: "Assign 2",
            pygame.K_3: "Assign 3",
            pygame.K_4: "Assign 4",
            pygame.K_5: "Assign 5",
            pygame.K_6: "Assign 6",
            pygame.K_7: "Assign 7",
            pygame.K_8: "Assign 8",
            pygame.K_9: "Assign 9"
        }
        self.current_margins = []
        self.current_labels = []
        self.output = {
            "x": [], "y": [], "w": [], "h": [], "l": [], "i": []
        }
        if not op.exists(self.output_fn):
            self.prev = pd.DataFrame(self.output)
        else:
            self.prev = pd.read_csv(self.output_fn, index_col=0)
        self.fns = list(
            filter(
                lambda x: x.split(".")[-1] in self.exts,
                [op.join(input_folder, b) for b in [a for a in os.walk(input_folder)][0][-1]]
            )
        )
        self.maxfn = len(self.fns)-1
        self.init_buttons()
        
    def annotate(self, coords1, coords2, image_size):
        """
        Construct yolo annotation from coordinates
        
        Params:
            coords1 - (x, y) of left top corner
            coords2 - (x, y) of right bottom corner
            image_size - (width, height) of an image in pixels
        """
        width = coords2[0]-coords1[0]
        height = coords2[1]-coords1[1]
        center_x = (coords1[0] + width/2)/image_size[0]
        center_y = (coords1[1] + height/2)/image_size[1]
        return(center_x, center_y, width/image_size[0], height/image_size[1])
            
    def plot_image(self, img):
        """
        Plot image
        
        Params:
            img - path to image
        """
        image = pygame.image.load(img)
        self.current_img_boundaries = image.get_rect()
        width = self.current_img_boundaries[2]
        height = self.current_img_boundaries[3]
        if width > 800 or height > 1000:
            largest = np.max([width, height])
            if largest == width:
                width = 800
                k = width/800
                height = height*k
            else:
                height = 1000
                k = height/1000
                width = width*k
            image = pygame.transform.scale(image, (int(width), int(height)))
        self.screen.blit(image, self.current_img_boundaries)
        
    def plot_bbox(self, x1, y1, x2, y2, color=(200,100,0)):
        """
        Plot bounding box
        
        Params:
            x1, y1, x2, y2 - coordinates of top left and bottom right
            color - color of the box
        """
        pygame.draw.rect(
            self.screen, color,
            (x1, y1, x2-x1, y2-y1), 2
        )
        
    def plot_clicked(self, coords):
        """
        Plot clicked point
        
        Params:
            coords - (x,y) position of cursor
        """
        pygame.draw.circle(
            self.screen, (200,0,0), coords, 4 
        )
        
    def init_buttons(self):
        """Initialize buttons"""
        self.buttons = {
            "Clear": (self.font.render("      Clear", True, (0,100,0)), (865, 50)),
            "Done&Next": (self.font.render("Done&Next", True, (0,100,0)), (975, 50))
        }
        current_X = 850
        current_Y = 160
        for a in range(self.number):
            if current_X > 1220:
                current_X = 850
                current_Y += 100
            caption = "Assign "+str(a)
            self.buttons[caption] = (
                self.font.render(caption, True, (0,100,100)), (current_X, current_Y)
            )
            current_X += 85
        
    def render_interface(self):
        """Render everything each millisecond"""
        current_img = self.fns[self.current_image_number]
        self.plot_image(current_img)
        for a in self.buttons:
            self.screen.blit(self.buttons[a][0], self.buttons[a][1])
        for a in self.mouse_pressed:
            self.plot_clicked(a)
        if len(self.mouse_pressed) == 2:
            self.plot_bbox(
                self.mouse_pressed[0][0],
                self.mouse_pressed[0][1],
                self.mouse_pressed[1][0],
                self.mouse_pressed[1][1],
            )
        text = self.font.render(self.action_label, True, (255,255,255))
        self.screen.blit(text, (950, 750))
        
    def clear(self):
        """Restart everything"""
        self.mouse_pressed = []
        self.current_margins = []
        self.current_labels = []
        self.output = {
            "x": [], "y": [], "w": [], "h": [], "l": [], "i": []
        }
        self.current_image_number = 0
        
    def assign(self, label):
        """
        Assign label to a bounding box
        
        Params:
            label - chosen label
        """
        if len(self.mouse_pressed) == 2:
            self.current_margins.append(self.mouse_pressed)
            self.mouse_pressed = []
            self.current_labels.append(label)
        
    def done_and_next(self):
        """Complete all operations and switch to the next image"""
        for a in self.current_margins:
            x, y, w, h = self.annotate(
                a[0], a[1], (self.current_img_boundaries[2], self.current_img_boundaries[3])
            )
            self.output["x"].append(x)
            self.output["y"].append(y)
            self.output["w"].append(w)
            self.output["h"].append(h)
            self.output["i"].append(self.fns[self.current_image_number])
        self.output["l"].extend(self.current_labels)
        self.mouse_pressed = []
        self.current_margins = []
        self.current_labels = []
        if self.current_image_number != self.maxfn:
            self.current_image_number += 1
        else:
            self.current_image_number = 0
            
    def save(self):
        """Save labellings to file"""
        df = pd.DataFrame(self.output, columns=["i", "l", "x", "y", "w", "h"])
        df = pd.concat([self.prev, df])
        df.to_csv(self.output_fn)
        
    def loop(self):
        """Main function"""
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    if event.key in self.keyboard.keys():
                        self.action_label = self.keyboard[event.key]
                        if self.keyboard[event.key] == "Clear":
                            self.clear()
                        elif "Assign" in self.keyboard[event.key]:
                            lbl = int(self.keyboard[event.key].split(" ")[-1])
                            if lbl < self.number:
                                self.assign(lbl)
                        elif self.keyboard[event.key] == "Done&Next":
                            self.done_and_next()
                        elif self.keyboard[event.key] == "Save":
                            self.save()
                if event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    if self.current_img_boundaries.collidepoint(*pos):
                        self.mouse_pressed.append(pos)
                    if len(self.mouse_pressed) > 2:
                        self.mouse_pressed = []
                    for a in self.buttons:
                        rect = self.buttons[a][0].get_rect()
                        rect[0] += self.buttons[a][1][0]
                        rect[1] += self.buttons[a][1][1]
                        rect[2] += self.buttons[a][1][0]
                        rect[3] += self.buttons[a][1][1]
                        if rect.collidepoint(*pos):
                            if a == "Clear":
                                self.clear()
                            elif a == "Done&Next":
                                self.done_and_next()
                            elif "Assign" in a:
                                lbl = int(a.split(" ")[-1])
                                if lbl < self.number:
                                    self.assign(lbl)
            self.screen.fill((0,0,0))
            self.render_interface()
            pygame.display.update()
            self.clock.tick(60)
            
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Labelapki - immersive pygame-based image labelling tool"
    )
    parser.add_argument(
        "inputF",
        metavar="Folder",
        action="store",
        help="Folder with images to label"
    )
    parser.add_argument(
        "outputF",
        metavar="File",
        action="store",
        help="Path to output file"
    )
    parser.add_argument(
        "numberL",
        metavar="labels",
        action="store",
        help="Number of possible labels"
    )
    args = parser.parse_args()
    app = App(args.inputF, args.outputF, int(args.numberL))
    app.loop()
    pygame.display.flip()