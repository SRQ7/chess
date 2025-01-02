import pygame as pg
import numpy as np
import sys, hashlib, copy

# Initialise pygame window with necessary variables
pg.init()
np.set_printoptions(linewidth=100)
display = pg.display.set_mode((1440, 960))
pg.display.set_caption("Chess")
clock = pg.time.Clock()
currentScreen = "login"
previousScreen = None
currentUser = None
isAdmin = False
running = True

# Colours
clrWhite = pg.Color("white")
clrBlack = pg.Color("black")
clrGrey = pg.Color("gray")
clrBlue = (59, 143, 227)

# Transition screen procedure
def changeScreen(newScreen):
    global previousScreen, currentScreen
    previousScreen = currentScreen
    currentScreen = newScreen

# SHA-256 hash function
def getHash(string):
    string = hashlib.sha256(string.encode()).hexdigest()
    return string

# Class for text file database
class Database:
    def __init__(self, textFile):
        self.file = textFile
        self.dict = self.getDict()

    # Convert text file to dictionary
    def getDict(self):
        file = open(self.file, "r")
        fileDict = file.readlines()
        fileDict = [line.strip() for line in fileDict]
        fileDict = "".join(fileDict)
        file.close()
        if fileDict != "":
            return eval(fileDict)
        else:
            return dict()

    # Update dictionary with current player stats
    def updateDict(self, player):
        if player.gamesPlayed > 0:
            player.winRate = round(player.gamesWon / player.gamesPlayed, 2)
        self.dict[player.name] = {'password': player.pwrd,
                                   'gamesPlayed': player.gamesPlayed,
                                   'gamesWon': player.gamesWon,
                                   'gamesLost': player.gamesLost,
                                   'winRate': player.winRate,
                                   'maxAiBeaten': player.maxAiBeaten
                                   }

    # Amend text file with current dictionary
    def updateFile(self):
        file = open(self.file, "w")
        file.write("{\n")
        keys = list(self.dict.keys())
        values = list(self.dict.values())
        for i in range(len(self.dict)):
            key = (keys[i])
            value = (values[i])
            if i == len(self.dict) - 1:
                file.write(f"'{key}': {value}\n")
            else:
                file.write(f"'{key}': {value},\n")
        file.write("}")
        file.close()

# Class for GUI boxes
class Box:
    def __init__(self, position, dimensions, colour):
        self.pos = position
        self.dim = dimensions
        self.clr = colour
        self.rect = pg.Rect(position, dimensions)
        self.surf = pg.Surface(dimensions)

    def draw(self):
        self.surf.fill(self.clr)
        display.blit(self.surf, self.pos)

    def drawImage(self, image):
        self.surf.fill(self.clr)
        self.surf.blit(image, (0,0))
        display.blit(self.surf, self.pos)

# Subclass for GUI text boxes (inherits from Box)
class Textbox(Box):
    def __init__(self, position, dimensions, colour, text, textSize, textColour, textOffset):
        super().__init__(position, dimensions, colour)
        self.txt = text
        self.txtSize = textSize
        self.txtClr = textColour
        self.txtOffset = textOffset
        self.txtFont = pg.font.Font("game_font.ttf", self.txtSize)

    def draw(self):
        self.surf.fill(self.clr)
        display.blit(self.surf, self.pos)
        display.blit(self.txtFont.render(self.txt, True, self.txtClr),
                     (self.rect.x + (self.txtOffset[0]), self.rect.y + (self.txtOffset[1])))

# Class for image
class Image:
    def __init__(self, imageFile, position):
        self.surf = pg.image.load(imageFile).convert_alpha()
        self.pos = position
        self.rect = self.surf.get_rect(topleft = self.pos)
        self.mask = pg.mask.from_surface(self.surf)

    def draw(self):
        display.blit(self.surf, self.pos)

# Class for human player
class Player:
    def __init__(self, username, password):
        self.name = username
        self.pwrd = password
        self.gamesPlayed = 0
        self.gamesWon = 0
        self.gamesLost = 0
        self.winRate = 0.00
        self.maxAiBeaten = 0

    # Fetch player stats from database
    def getStats(self, database):
        self.gamesPlayed = database.dict[self.name]['gamesPlayed']
        self.gamesWon = database.dict[self.name]['gamesWon']
        self.gamesLost = database.dict[self.name]['gamesLost']
        self.winRate = database.dict[self.name]['winRate']
        self.maxAiBeaten = database.dict[self.name]['maxAiBeaten']

# Class for chess board
class Board:
    def __init__(self):
        self.array = np.full((8, 8), fill_value = None)
        self.arrangeStartPos()

    # Return human-readable chess board if (self) object called as string
    def __str__(self):
        readableArray = np.full((8,8), fill_value = None)
        for i in range(8):
            for j in range(8):
                pieceObj = self.array[i][j]
                if pieceObj != None:
                    readableArray[i][j] = f"{pieceObj.clr[0]}_{pieceObj.type}"
        return str(readableArray)

    # Set pieces in their starting position for a standard chess game
    def arrangeStartPos(self):
        backlinePieces = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        for i in range(2, 6):
            for j in range(8):
                self.array[i][j] = None
        for i in range(8):
            self.placePiece(Pieces("pawn", "black"), (1, i))
            self.placePiece(Pieces("pawn", "white"), (6, i))
        for i in range(0, 8):
            self.placePiece(Pieces(backlinePieces[i], "black"), (0, i))
            self.placePiece(Pieces(backlinePieces[i], "white"), (7, i))

    # Place a given piece object in desired position
    def placePiece(self, pieceObject, position):
        self.array[position[0]][position[1]] = pieceObject

class Pieces:
    def __init__(self, pieceType, pieceColour):
        self.type = pieceType
        self.clr = pieceColour

# Create local mode
chessBoard = Board()
print(chessBoard)

# Create AI mode

# Initialise database
db = Database("users.txt")

# Create back button (previous screen)
backButtonImg = Image("back_button.png", (0,0))

# Create login screen
usernameBox = Textbox((420, 350), (600, 50), clrWhite, "", 40, clrBlack, (5, -4))
passwordBox = Textbox((420, 410), (600, 50), clrWhite, "", 40, clrBlack, (5, -4))
loginBox = Textbox((565, 470), (120, 55), clrWhite, "LOGIN", 40, clrBlack, (5, -2))
registerBox = Textbox((695, 470), (190, 55), clrWhite, "REGISTER", 40, clrBlack, (5, -2))
loginScreenBoxes = [usernameBox, passwordBox, loginBox, registerBox]

# Create main menu
localModeBox = Textbox((525, 275), (400, 80), clrWhite, "Local 2-Player", 50, clrBlack, (35, -2))
aiModeBox = Textbox((525, 380), (400, 80), clrWhite, "AI Opponent", 50, clrBlack, (53, -2))
statsAndConfigBox = Textbox((525, 485), (400, 80), clrWhite, "Stats & Config", 50, clrBlack, (40, -2))
mainMenuBoxes = [localModeBox, aiModeBox, statsAndConfigBox]

# Create stats and config screen
userStatsBox = Textbox((210,170), (270,50), clrBlue, "User Statistics", 35, clrWhite, (20, 2))
gamesPlayedBox = Textbox((140,230), (410,100), clrWhite, f"Games played: ", 45, clrBlack, (30, 12))
gamesWonBox = Textbox((140,350), (410,100), clrWhite, f"Games won: ", 45, clrBlack, (50, 12))
gamesLostBox = Textbox((140,470), (410,100), clrWhite, f"Games lost: ", 45, clrBlack, (50, 12))
winRateBox = Textbox((140,590), (410,100), clrWhite, f"Winrate: %", 45, clrBlack, (50, 12))
maxAiBeatenBox = Textbox((140,710), (410,100), clrWhite, f"Max AI beaten: ", 45, clrBlack, (35, 12))
usernameDisplayBox = Textbox((600,440), (600,150), clrWhite, f"Username: ", 60, clrBlack, (50, 27))
searchUserDisplayBox = Textbox((600,380), (220,50), clrBlue, "Search user:", 35, clrWhite, (10, -5))
statsConfBoxes = [userStatsBox, gamesPlayedBox, gamesWonBox, gamesLostBox, winRateBox, maxAiBeatenBox, usernameDisplayBox]
# Create admin only options for this screen
userLookupBox = Textbox((820,380), (380,50), clrWhite, "", 35, clrBlack, (10, -5))
searchButtonImg = Image("search_button.png", (1200,380))
statsViewUser = Player(None, None)

# Main loop
while running == True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        # Login screen logic
        if currentScreen == "login":
            if event.type == pg.MOUSEBUTTONDOWN:
                # If user clicks user/pass box then colour it to select it
                if usernameBox.rect.collidepoint(event.pos):
                    passwordBox.clr, usernameBox.clr = clrWhite, clrGrey
                elif passwordBox.rect.collidepoint(event.pos):
                    usernameBox.clr, passwordBox.clr = clrWhite, clrGrey

                # If user clicks register box then validate inputs + add entry to DB
                elif registerBox.rect.collidepoint(event.pos):
                    if len(usernameBox.txt) < 3 or len(passwordBox.txt) < 6:
                        print("Ensure your username is at least 3 characters long, "
                              "and your password is at least 6 characters long.")
                    elif usernameBox.txt not in db.dict:
                        currentUser = Player(usernameBox.txt, getHash(passwordBox.txt))
                        db.updateDict(currentUser)
                        statsViewUser = copy.deepcopy(currentUser)
                        changeScreen("menu")
                    else:
                        print("Username already exists.")

                # If user clicks login box then validate inputs + retrieve player stats from DB
                elif loginBox.rect.collidepoint(event.pos):
                    if usernameBox.txt in db.dict and getHash(passwordBox.txt) == db.dict[usernameBox.txt]['password']:
                        currentUser = Player(usernameBox.txt, getHash(passwordBox.txt))
                        currentUser.getStats(db)
                        statsViewUser = copy.deepcopy(currentUser)
                        if currentUser.name == "Mikee":
                            isAdmin = True
                        changeScreen("menu")
                    else:
                        print("Account does not exist.")

                else:
                    usernameBox.clr = passwordBox.clr = clrWhite

            elif event.type == pg.KEYDOWN:
                # Collect user/pass inputs
                if usernameBox.clr == clrGrey:
                    if event.key == pg.K_RETURN:
                        usernameBox.clr = clrWhite
                    elif event.key == pg.K_BACKSPACE:
                        usernameBox.txt = usernameBox.txt[:-1]
                    elif len(usernameBox.txt) <= 8 and event.unicode.isalnum():
                        usernameBox.txt += event.unicode

                elif passwordBox.clr == clrGrey:
                    if event.key == pg.K_RETURN:
                        passwordBox.clr = clrWhite
                    elif event.key == pg.K_BACKSPACE:
                        passwordBox.txt = passwordBox.txt[:-1]
                    elif len(passwordBox.txt) <= 12 and event.unicode.isalnum():
                        passwordBox.txt += event.unicode

        # Main menu logic
        elif currentScreen == "menu":
            if event.type == pg.MOUSEBUTTONDOWN:
                if localModeBox.rect.collidepoint(event.pos):
                    changeScreen("local")
                elif aiModeBox.rect.collidepoint(event.pos):
                    changeScreen("ai")
                elif statsAndConfigBox.rect.collidepoint(event.pos):
                    changeScreen("statsConf")

        # Local mode logic
        elif currentScreen == "local":
            if event.type == pg.MOUSEBUTTONDOWN:
                if backButtonImg.rect.collidepoint(event.pos):
                    if backButtonImg.mask.get_at(event.pos):
                        changeScreen("menu")

        # AI mode logic
        elif currentScreen == "ai":
            if event.type == pg.MOUSEBUTTONDOWN:
                if backButtonImg.rect.collidepoint(event.pos):
                    if backButtonImg.mask.get_at(event.pos):
                        changeScreen("menu")

        # Stats and config screen logic
        elif currentScreen == "statsConf":
            # If viewing own account stats, catch any changes made during session in real time
            if currentUser.name == statsViewUser.name:
                statsViewUser = copy.deepcopy(currentUser)
            # Update text boxes with player stats
            gamesPlayedBox.txt = f"Games played: {statsViewUser.gamesPlayed}"
            gamesWonBox.txt = f"Games won: {statsViewUser.gamesWon}"
            gamesLostBox.txt = f"Games lost: {statsViewUser.gamesLost}"
            winRateBox.txt = f"Winrate: {statsViewUser.winRate*100}%"
            maxAiBeatenBox.txt = f"Max AI beaten: {statsViewUser.maxAiBeaten}"
            usernameDisplayBox.txt = f"Username: {statsViewUser.name}"

            if event.type == pg.MOUSEBUTTONDOWN:
                if backButtonImg.rect.collidepoint(event.pos):
                    if backButtonImg.mask.get_at(event.pos):
                        changeScreen("menu")

                # If admin clicks user lookup box then colour it to select it
                elif userLookupBox.rect.collidepoint(event.pos) and isAdmin == True:
                    userLookupBox.clr = clrGrey

                # If admin clicks search button then validate input and change currentUser to desired lookup
                # Masks start at (0,0) therefore offset of -1200(x) and -380(y) is needed to detect click
                elif searchButtonImg.rect.collidepoint(event.pos):
                    if searchButtonImg.mask.get_at((event.pos[0]-1200,event.pos[1]-380)):
                        if userLookupBox.txt in db.dict:
                            statsViewUser = Player(userLookupBox.txt, None)
                            statsViewUser.getStats(db)
                        else:
                            print("Username does not exist.")

                else:
                    userLookupBox.clr = clrWhite

            elif event.type == pg.KEYDOWN:
                # Collect username lookup input
                if userLookupBox.clr == clrGrey:
                    if event.key == pg.K_RETURN:
                        userLookupBox.clr = clrWhite
                    elif event.key == pg.K_BACKSPACE:
                        userLookupBox.txt = userLookupBox.txt[:-1]
                    elif len(userLookupBox.txt) <= 8 and event.unicode.isalnum():
                        userLookupBox.txt += event.unicode

    # Draw login screen
    if currentScreen == "login":
        display.fill(clrBlue)
        for box in loginScreenBoxes:
            box.draw()

    # Draw main menu
    elif currentScreen == "menu":
        display.fill(clrBlue)
        for box in mainMenuBoxes:
            box.draw()

    # Draw local mode
    elif currentScreen == "local":
        display.fill(clrBlue)
        backButtonImg.draw()

    # Draw AI mode
    elif currentScreen == "ai":
        display.fill(clrBlue)
        backButtonImg.draw()

    # Draw stats and config screen
    elif currentScreen == "statsConf":
        display.fill(clrBlue)
        for box in statsConfBoxes:
            box.draw()
        if isAdmin == True:
            searchUserDisplayBox.draw()
            userLookupBox.draw()
            searchButtonImg.draw()

    # Updates
    if currentUser != None:
        db.updateDict(currentUser)
    db.updateFile()
    pg.display.update()
    clock.tick(240)

pg.quit()
sys.exit()