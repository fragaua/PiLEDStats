from PIL import Image, ImageDraw, ImageFont
from PIInfo import PIInfo
from typing import List


class PIInfoPage:

    '''
        Uses the ImageDraw <draw> object to draw all PIInfo objects in <info_list> onto the oled screen

        #    Top zone	 #
        #----------------#
        #       |        #
        #  Lt   |   Rt   #
        #       |        #
        #       |        #
        ##################

        The idea is to use the zones shown in the previous image to draw multiple information.
        When we configure we say where we want to draw a certain piece of information.
        Information can only be drawn if it fits the zone.
        
    '''

    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6)
      
    def __init__(self, info_list: List[PIInfo], draw: ImageDraw, display_size: tuple, grid: tuple, gap: int = 5):

        self.grid_col = grid[1]
        self.grid_row = grid[0]

        # Initialize grid with proposed size
        self.grid = [[None for i in range(self.grid_col)] for j in range(self.grid_row)]

        self.gap = gap

        self.display_width = display_size[0]
        self.display_height = display_size[1]

        self.infos = info_list
        self.d = draw

        # Place each info from 1D array into a lot in the XD grid
        for i, info in enumerate(self.infos):
            x_idx = i // self.grid_col 
            y_idx = i % self.grid_col
            self.grid[x_idx][y_idx] = info
        print(self.grid)
        self.last_drawn_info = None # Used to help the calculation of the position of the next info to draw

    def draw(self):
        self._clearscreen()
        for i in range(self.grid_row):
            for j in range(self.grid_col):
                if self.grid[i][j] is not None:
                    info = self.grid[i][j].fetch()
                    textwidth = self._textwidth(self.last_drawn_info) + self.gap if self.last_drawn_info is not None else 0
                    self._writetext(((j * textwidth), i * 10), info)
                    self.last_drawn_info = info

    


    # Returns total width, in pixels, that a certain text ocupies with a certain font and font size 
    def _textwidth(self, text, font=FONT):
        return round(self.d.textlength(text, font=font))
    
    ## Simple wrapper
    def _writetext(self, pos, text, font=FONT):
        self.d.text(pos, text, font=font, fill=255)

    def _clearscreen(self):
        self.d.rectangle((0, 0, self.display_width, self.display_height * 2), outline=0, fill=0)
