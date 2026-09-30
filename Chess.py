import pygame as pg
import numpy as np
import sys, hashlib, copy
import ast

# Initialise pygame window with necessary variables
pg.init()
display = pg.display.set_mode((1440, 960))
pg.display.set_caption("Chess")
clock = pg.time.Clock()
currentScreen = "login"
previousScreen = None
currentUser = None
isAdmin = False
running = True
testMove = False
indicatedLegalMoves = []

# Colours
clrWhite = pg.Color("white")
clrBlack = pg.Color("black")
clrSelected = pg.Color("gray")
clrBlue = (59, 143, 227)
clrRed = (210, 4, 45)
clrLightSquare = (89, 89, 89)
clrDarkSquare = (54, 54, 54)
clrLegalSquare = (0, 255, 0)
clrOptimalSquare = (191, 64, 191)

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
        try:
            file = open(self.file, "r")
        except FileNotFoundError:
            return dict()
        fileDict = file.readlines()
        fileDict = [line.strip() for line in fileDict]
        fileDict = "".join(fileDict)
        file.close()
        if fileDict != "":
            return ast.literal_eval(fileDict)
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
        self.txtFont = pg.font.Font("assets/game_font.ttf", self.txtSize)

    def draw(self):
        self.surf.fill(self.clr)
        display.blit(self.surf, self.pos)
        display.blit(self.txtFont.render(self.txt, True, self.txtClr),
                     (self.rect.x + (self.txtOffset[0]), self.rect.y + (self.txtOffset[1])))

# Class for image
class Image:
    def __init__(self, imageFile, position):
        self.name = imageFile
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

class Board:
    def __init__(self):
        self.array = np.full((8, 8), fill_value = None)
        self.guiArray = np.full((8, 8), fill_value = None)
        self.prevMoves = []
        self.legalMoves = []
        self.turn = "white"
        self.kingInCheck = False
        self.gameResult = None

        # Vectorise functions to apply them to arrays instead of single items
        self.convToReadable = np.vectorize(self.convPcToReadable)
        self.convToValue = np.vectorize(self.convPcToValue)

        # Prerequisites for game
        self.arrangeStartPos()
        self.updateLegalMoves()

    # Return human-readable chess board if (self) object called as string
    def __str__(self):
        readableArray = self.convToReadable(self.array)
        return str(readableArray)

    # Convert piece to readable string
    def convPcToReadable(self, piece):
        readablePiece = None
        if piece != None:
            readablePiece = f"{piece.clr[0]}_{piece.type}"
        return readablePiece

    # Convert piece to its value
    def convPcToValue(self, piece):
        value = 0.0
        if piece != None:
            value = piece.value
        return value

    # Check if position in board
    def posValid(self, pos):
        if (pos[0] >= 0 and pos[0] <= 7) and (pos[1] >= 0 and pos[1] <= 7):
            return True
        else:
            return False

    # Get colour of a position
    def posColour(self, pos):
        piece = self.array[pos]
        if piece == None:
            return None
        else:
            return piece.clr

    # Flip turn
    def flipTurn(self):
        if self.turn == "white":
            self.turn = "black"
        else:
            self.turn = "white"

    ## Pseudo => without considering putting own king in check
    # Get pseudo straight-line legal moves
    def pseudoStraightMoves(self, pos):
        piece = self.array[pos]
        x = pos[1]
        y = pos[0]
        possibleMoves = []

        ## COMMENTS OF THIS LOOP CAN BE REFERRED TO WHEN LOOKING AT:
        ## pseudoStraightMoves, pseudoDiagonalMoves, getPseudoLegalMoves
        # Vertical movement (current pos -> up)
        for i in range(y-1, -1, -1):
            # Assign position that is being currently examined to tempPos variable
            tempPos = (i, x)
            if self.posValid(tempPos):
                # Get colour of piece occupying tempPos
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    # If empty square continue traversing in same direction
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    # If friendly square stop traversing
                    break
                else:
                    # If enemy square add move to possibleMoves and stop traversing
                    possibleMoves.append((pos, tempPos))
                    break
        # Vertical movement (current pos -> down)
        for i in range(y+1, 8):
            tempPos = (i, x)
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break

        # Horizontal movement (current pos -> left)
        for i in range(x-1, -1, -1):
            tempPos = (y, i)
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break
        # Horizontal movement (current pos -> right)
        for i in range(x+1, 8):
            tempPos = (y, i)
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break

        return possibleMoves

    def pseudoDiagonalMoves(self, pos):
        piece = self.array[pos]
        x = pos[1]
        y = pos[0]
        possibleMoves = []

        # Up-right movement (current pos -> top_right)
        traversal_x_values = range(x+1, 8)
        traversal_y_values = range(y-1, -1, -1)
        traversal_length = min(len(traversal_x_values), len(traversal_y_values))
        for i in range(traversal_length):
            tempPos = (traversal_y_values[i], traversal_x_values[i])
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break
        # Down-right movement (current pos -> bottom_right)
        traversal_x_values = range(x+1, 8)
        traversal_y_values = range(y+1, 8)
        traversal_length = min(len(traversal_x_values), len(traversal_y_values))
        for i in range(traversal_length):
            tempPos = (traversal_y_values[i], traversal_x_values[i])
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break

        # Up-left movement (current pos -> top_left)
        traversal_x_values = range(x-1, -1, -1)
        traversal_y_values = range(y-1, -1, -1)
        traversal_length = min(len(traversal_x_values), len(traversal_y_values))
        for i in range(traversal_length):
            tempPos = (traversal_y_values[i], traversal_x_values[i])
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break
        # Down-left movement (current pos -> bottom_left)
        traversal_x_values = range(x-1, -1, -1)
        traversal_y_values = range(y+1, 8)
        traversal_length = min(len(traversal_x_values), len(traversal_y_values))
        for i in range(traversal_length):
            tempPos = (traversal_y_values[i], traversal_x_values[i])
            if self.posValid(tempPos):
                clrCheck = self.posColour(tempPos)
                if clrCheck == None:
                    possibleMoves.append((pos, tempPos))
                elif clrCheck == piece.clr:
                    break
                else:
                    possibleMoves.append((pos, tempPos))
                    break

        return possibleMoves

    # Check if current turn's colour is in check
    def inCheck(self):
        # Traverse from king's pos as each of these pieces to detect danger
        traverseTypes = ["queen", "rook", "bishop", "knight", "pawn"]
        inCheck = False

        # Iterate through array to find king
        for i in range(8):
            for j in range(8):
                if self.array[i][j] != None:
                    piece = Pieces(self.array[i][j].type, self.array[i][j].clr)
                    # Ensure king is the desired colour
                    if piece.type == "king" and piece.clr == self.turn:
                        for type in traverseTypes:
                            self.array[i][j] = Pieces(type, self.turn)
                            moves = self.getPseudoLegalMoves((i, j))
                            # If test piece can move to enemy square and is of the same type, king's in check
                            for move in moves:
                                enemySqr = self.array[move[1]]
                                if enemySqr != None:
                                    if enemySqr.clr != piece.clr and enemySqr.type == type:
                                        inCheck = True
                        # Replace test piece with original king
                        self.array[i][j] = Pieces("king", self.turn)
        return inCheck

    # Get all pseudo legal moves for a position
    def getPseudoLegalMoves(self, pos):
        piece = self.array[pos]
        x = pos[1]
        y = pos[0]
        possibleMoves = []
        if piece != None:
            straightMoves = self.pseudoStraightMoves(pos)
            diagonalMoves = self.pseudoDiagonalMoves(pos)

            # Loop through each possible move for corresponding piece
            # If the move is valid, add it to possibleMoves
            if piece.type == "king":
                # Vertical movement (up -> current pos -> down)
                for i in range(y-1, y+2):
                    # Horizontal movement (left -> current pos -> right)
                    for j in range(x-1, x+2):
                        tempPos = (i, j)
                        # Ensure tempPos is valid board index and skip current pos of piece
                        if self.posValid(tempPos):
                            if tempPos != pos:
                                clrCheck = self.posColour(tempPos)
                                # Ensure tempPos not occupied by friendly colour
                                if clrCheck != piece.clr:
                                    possibleMoves.append((pos, tempPos))

            elif piece.type == "queen":
                if straightMoves != []:
                    possibleMoves.extend(straightMoves)
                if diagonalMoves != []:
                    possibleMoves.extend(diagonalMoves)

            elif piece.type == "rook":
                if straightMoves != []:
                    possibleMoves.extend(straightMoves)

            elif piece.type == "bishop":
                if diagonalMoves != []:
                    possibleMoves.extend(diagonalMoves)

            elif piece.type == "knight":
                # Above-piece movement (2left1up -> 1left2up -> 1right2up, 2right1up)
                traversal_x_values = [x-2, x-1, x+1, x+2]
                traversal_y_values = [y-1, y-2, y-2, y-1]
                for i in range(4):
                    tempPos = (traversal_y_values[i], traversal_x_values[i])
                    if self.posValid(tempPos):
                        clrCheck = self.posColour(tempPos)
                        if clrCheck != piece.clr:
                            possibleMoves.append((pos, tempPos))
                # Below-piece movement (2left1down -> 1left2down -> 1right2down -> 2right1down)
                traversal_y_values = [y+1, y+2, y+2, y+1]
                for i in range(4):
                    tempPos = (traversal_y_values[i], traversal_x_values[i])
                    if self.posValid(tempPos):
                        clrCheck = self.posColour(tempPos)
                        if clrCheck != piece.clr:
                            possibleMoves.append((pos, tempPos))

            elif piece.type == "pawn":
                # Traverse up for white pawn and down for black pawn
                if piece.clr == "white":
                    traversal_y_values = [y-1, y-2]
                else:
                    traversal_y_values = [y+1, y+2]
                if piece.moved == False:
                    # Pawn can move forward 2 spaces on first move
                    for i in traversal_y_values:
                        tempPos = (i, x)
                        if self.posValid(tempPos):
                            clrCheck = self.posColour(tempPos)
                            if clrCheck == None:
                                possibleMoves.append((pos, tempPos))
                            else:
                                break
                else:
                    # Pawn can move forward 1 space after first move
                    tempPos = (traversal_y_values[0], x)
                    if self.posValid(tempPos):
                        clrCheck = self.posColour(tempPos)
                        if clrCheck == None:
                            possibleMoves.append((pos, tempPos))
                # Iterate through diagonal squares
                for i in range(-1, 2, 2):
                    tempPos = (traversal_y_values[0], x+i)
                    if self.posValid(tempPos):
                        clrCheck = self.posColour(tempPos)
                        # If tempPos occupied by enemy, add move to possibleMoves
                        if clrCheck not in (None, piece.clr):
                            possibleMoves.append((pos, tempPos))

        return possibleMoves

    # Get all legal moves for a position
    def getLegalMoves(self, pos):
        possibleMoves = self.getPseudoLegalMoves(pos)
        legalMoves = []
        shiftedPc = (self.array[pos].type, self.array[pos].clr, self.array[pos].moved)

        # If king's in check after the simulated move it's illegal
        for move in possibleMoves:
            # Save attributes for piece that can be captured
            takenPc = None
            if self.array[move[1]] != None:
                takenPc = (self.array[move[1]].type, self.array[move[1]].clr, self.array[move[1]].moved)
            # Simulate move
            self.array[move[1]] = Pieces(shiftedPc[0], shiftedPc[1])
            self.array[pos] = None
            # If king not in check after move, it's a legal move so add to list
            if self.inCheck() != True:
                legalMoves.append(move)
            # Undo the simulated move and restore original board
            self.array[pos] = Pieces(shiftedPc[0], shiftedPc[1])
            self.array[pos].moved = shiftedPc[2]
            if takenPc != None:
                self.array[move[1]] = Pieces(takenPc[0], takenPc[1])
                self.array[move[1]].moved = takenPc[2]
            else:
                self.array[move[1]] = None

        return legalMoves

    # Update all available legal moves for board
    def updateLegalMoves(self):
        self.legalMoves = []
        for i in range(8):
            for j in range(8):
                piece = self.array[i][j]
                if piece != None:
                    # If piece is of the same colour then attach its legal moves to board attribute
                    if piece.clr == self.turn:
                        self.legalMoves.extend(self.getLegalMoves((i, j)))

    # Get the optimal move for current board state
    def getOptimalMove(self, depth, alpha, beta):
        # If at terminal player node without being in checkmate
        if depth == 0 or self.gameResult != None:
            if self.gameResult == "white":
                currentEval = self.eval() + 500
            elif self.gameResult == "black":
                currentEval = self.eval() - 500
            else:
                currentEval = self.eval()
            return None, currentEval

        # If neither at max depth nor in checkmate
        else:
            # Maximise
            if self.turn == "white":
                maxEval = float('-inf')
                bestMove = None
                for move in self.legalMoves:
                    global testMove
                    testMove = True
                    self.move(move[0], move[1])
                    optimalMove = self.getOptimalMove(depth-1, alpha, beta)
                    self.undoMove()
                    testMove = False
                    if optimalMove[1] > maxEval:
                        maxEval = optimalMove[1]
                        bestMove = move
                    alpha = max(alpha, maxEval)
                    if beta <= alpha:
                        break
                return bestMove, maxEval

            # Minimise
            elif self.turn == "black":
                minEval = float('inf')
                bestMove = None
                for move in self.legalMoves:
                    testMove = True
                    self.move(move[0], move[1])
                    optimalMove = self.getOptimalMove(depth-1, alpha, beta)
                    self.undoMove()
                    testMove = False
                    if optimalMove[1] < minEval:
                        minEval = optimalMove[1]
                        bestMove = move
                    beta = min(beta, minEval)
                    if beta <= alpha:
                        break
                return bestMove, minEval

    # Return board value using only material based evaluation
    def eval(self):
        valueArray = self.convToValue(self.array)
        totalValue = np.sum(valueArray)
        return totalValue

    # Set starting position for a standard chess game
    def arrangeStartPos(self):
        # Set board
        for i in range(8):
            for j in range(8):
                if i % 2 == j % 2:
                    self.guiArray[i][j] = Box((375 + j*90, 100 + i*90), (90, 90), clrLightSquare)
                else:
                    self.guiArray[i][j] = Box((375 + j*90, 100 + i*90), (90,90), clrDarkSquare)

        # Set pieces
        backlinePieces = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        for i in range(2, 6):
            for j in range(8):
                self.array[i][j] = None
        for i in range(8):
            self.place(Pieces("pawn", "black"), (1, i))
            self.place(Pieces("pawn", "white"), (6, i))
        for i in range(8):
            self.place(Pieces(backlinePieces[i], "black"), (0, i))
            self.place(Pieces(backlinePieces[i], "white"), (7, i))

    # Place a given piece in desired position
    def place(self, piece, pos):
        self.array[pos[0]][pos[1]] = piece

    # Move a piece to desired position
    def move(self, pos1, pos2):
        # Append upcoming move position changes and data for piece taken and moved to previous moves list
        # If no piece taken, use NoneType to represent it
        if self.array[pos2] == None:
            self.prevMoves.append((pos1, pos2, None, self.array[pos1].moved))
        else:
            # Format of item in prevMoves: (pos1, pos2, (takenPcType, takenPcClr, takenPcMoved), shiftedPcMoved)
            self.prevMoves.append((pos1, pos2, (self.array[pos2].type, self.array[pos2].clr, self.array[pos2].moved),
                                   self.array[pos1].moved))

        # Copy current piece object to new position and empty old position
        self.array[pos2] = Pieces(self.array[pos1].type, self.array[pos1].clr)
        self.array[pos1] = None
        self.array[pos2].moved = True
        # Flip turn and update check status as well as legal moves attribute
        self.flipTurn()
        self.kingInCheck = self.inCheck()
        self.updateLegalMoves()
        # Check game end conditions
        global testMove
        if not testMove:
            # End game if checkmate
            if self.kingInCheck and self.legalMoves == []:
                if self.turn == "white":
                    self.gameResult = "black"
                    print("Black has won the game with a checkmate!")
                    currentUser.gamesPlayed += 1
                    currentUser.gamesLost += 1
                else:
                    self.gameResult = "white"
                    print("White has won the game with a checkmate!")
                    currentUser.gamesPlayed += 1
                    currentUser.gamesWon += 1
            # End game if stalemate
            elif not self.kingInCheck and self.legalMoves == []:
                self.gameResult = None
                print("Game has ended in a stalemate.")
                currentUser.gamesPlayed += 1


    def undoMove(self):
        prevMove = self.prevMoves.pop()
        # Replace previous position of piece with copy of piece from current position
        self.array[prevMove[0]] = Pieces(self.array[prevMove[1]].type, self.array[prevMove[1]].clr)
        self.array[prevMove[0]].moved = prevMove[3]
        # Replace current position with piece that was taken
        if prevMove[2] == None:
            self.array[prevMove[1]] = None
        else:
            self.array[prevMove[1]] = Pieces(prevMove[2][0], prevMove[2][1])
            self.array[prevMove[1]].moved = [prevMove[2][2]]
        # Flip turn and update check status as well as legal moves attribute
        self.flipTurn()
        self.kingInCheck = self.inCheck()
        self.updateLegalMoves()
        # Check game end conditions
        global testMove
        if not testMove:
            # End game if checkmate
            if self.kingInCheck and self.legalMoves == []:
                if self.turn == "white":
                    self.gameResult = "black"
                    print("Black has won the game with a checkmate!")
                    currentUser.gamesPlayed += 1
                    currentUser.gamesLost += 1
                else:
                    self.gameResult = "white"
                    print("White has won the game with a checkmate!")
                    currentUser.gamesPlayed += 1
                    currentUser.gamesWon += 1
            # End game if stalemate
            elif not self.kingInCheck and self.legalMoves == []:
                self.gameResult = None
                print("Game has ended in a stalemate.")
                currentUser.gamesPlayed += 1


    def draw(self):
        pieceImgOffset = (17, 15)
        # Draw board
        for i in range(8):
            for j in range(8):
                self.guiArray[i][j].draw()
                # Draw pieces
                piece = self.array[i][j]
                if piece != None:
                    piecePos = (self.guiArray[i][j].pos[0] + pieceImgOffset[0], self.guiArray[i][j].pos[1] + pieceImgOffset[1])
                    pieceImg = Image(f"assets/pieces/{piece.clr[0]}_{piece.type}.png", piecePos)
                    pieceImg.draw()

class Pieces:
    def __init__(self, pieceType, pieceColour):
        self.type = pieceType
        self.clr = pieceColour
        self.moved = False
        self.value = self.getValue()

    def getValue(self):
        value = 0
        if self.type == "king":
            value = 200
        elif self.type == "queen":
            value = 9
        elif self.type == "rook":
            value = 5
        elif self.type == "bishop":
            value = 3
        elif self.type == "knight":
            value = 3
        elif self.type == "pawn":
            value = 1
        if self.clr == "black":
            value = -value
        return value

# Initialise database
db = Database("users.txt")

# Create login screen
usernameBox = Textbox((420, 350), (600, 50), clrWhite, "", 40, clrBlack, (5, -4))
passwordBox = Textbox((420, 410), (600, 50), clrWhite, "", 40, clrBlack, (5, -4))
loginBox = Textbox((565, 470), (120, 55), clrWhite, "LOGIN", 40, clrBlack, (5, -2))
registerBox = Textbox((695, 470), (190, 55), clrWhite, "REGISTER", 40, clrBlack, (5, -2))
alertBox = Textbox((420, 290), (600, 50), clrBlue, "", 30, clrRed, (-45, -4))
loginScreenBoxes = [usernameBox, passwordBox, loginBox, registerBox, alertBox]

# Create back button (go to previous screen)
backButtonImg = Image("assets/buttons/back_button.png", (0,0))

# Create main menu
localModeBox = Textbox((525, 275), (400, 80), clrWhite, "Local 2-Player", 50, clrBlack, (35, -2))
aiModeBox = Textbox((525, 380), (400, 80), clrWhite, "AI Opponent", 50, clrBlack, (53, -2))
statsAndConfigBox = Textbox((525, 485), (400, 80), clrWhite, "Stats & Config", 50, clrBlack, (40, -2))
mainMenuBoxes = [localModeBox, aiModeBox, statsAndConfigBox]

# Create local/AI modes
localBoard = Board()
aiBoard = Board()

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
searchButtonImg = Image("assets/buttons/search_button.png", (1200,380))
statsViewUser = None

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
                    passwordBox.clr, usernameBox.clr = clrWhite, clrSelected
                elif passwordBox.rect.collidepoint(event.pos):
                    usernameBox.clr, passwordBox.clr = clrWhite, clrSelected

                # If user clicks register box then validate inputs + add entry to DB
                elif registerBox.rect.collidepoint(event.pos):
                    if len(usernameBox.txt) < 3:
                        alertBox.txt = "Ensure your username is at least 3 characters long."
                    elif len(passwordBox.txt) < 6:
                        alertBox.txt = "Ensure your password is at least 6 characters long."
                    elif usernameBox.txt not in db.dict:
                        currentUser = Player(usernameBox.txt, getHash(passwordBox.txt))
                        db.updateDict(currentUser)
                        statsViewUser = copy.deepcopy(currentUser)
                        if currentUser.name == "Admin":
                            isAdmin = True
                        changeScreen("menu")
                    else:
                        print("Username already exists.")

                # If user clicks login box then validate inputs + retrieve player stats from DB
                elif loginBox.rect.collidepoint(event.pos):
                    if usernameBox.txt in db.dict and getHash(passwordBox.txt) == db.dict[usernameBox.txt]['password']:
                        currentUser = Player(usernameBox.txt, getHash(passwordBox.txt))
                        currentUser.getStats(db)
                        statsViewUser = copy.deepcopy(currentUser)
                        if currentUser.name == "Admin":
                            isAdmin = True
                        changeScreen("menu")
                    else:
                        print("Account does not exist.")

                else:
                    usernameBox.clr = passwordBox.clr = clrWhite

            elif event.type == pg.KEYDOWN:
                # Collect user/pass inputs
                if usernameBox.clr == clrSelected:
                    if event.key == pg.K_RETURN:
                        usernameBox.clr = clrWhite
                    elif event.key == pg.K_BACKSPACE:
                        usernameBox.txt = usernameBox.txt[:-1]
                    elif len(usernameBox.txt) <= 8 and event.unicode.isalnum():
                        usernameBox.txt += event.unicode

                elif passwordBox.clr == clrSelected:
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

        # Local/AI mode logic
        elif currentScreen in ("local", "ai"):
            # Get board corresponding with mode
            if currentScreen == "local":
                currentBoard = localBoard
            else:
                currentBoard = aiBoard

            # Only continue game logic if it hasn't ended
            if currentBoard.gameResult == None:
                if event.type == pg.MOUSEBUTTONDOWN:
                    if backButtonImg.rect.collidepoint(event.pos):
                        if backButtonImg.mask.get_at(event.pos):
                            changeScreen("menu")
                    else:
                        # Loop through chessboard
                        for i in range(8):
                            for j in range(8):
                                squareImg = currentBoard.guiArray[i][j]
                                piece = currentBoard.array[i][j]
                                # If user clicks one of their pieces then select it
                                if squareImg.rect.collidepoint(event.pos) and squareImg.clr != clrLegalSquare:
                                    if piece != None:
                                        if piece.clr == currentBoard.turn:
                                            squareImg.clr = clrSelected
                                # If user clicks on an indicated legal move pos then move the piece to that location
                                # Highlight the previous optimal move after the player move has been made
                                elif squareImg.rect.collidepoint(event.pos) and squareImg.clr == clrLegalSquare:
                                    for move in indicatedLegalMoves:
                                        if move[1] == (i, j):
                                            # Colour the initial and final positions of the optimal move
                                            previousOptimalMove = currentBoard.getOptimalMove(3, float('-inf'), float('inf'))
                                            currentBoard.guiArray[previousOptimalMove[0][0]].clr = clrOptimalSquare
                                            currentBoard.guiArray[previousOptimalMove[0][1]].clr = clrOptimalSquare
                                            # Perform move
                                            currentBoard.move(move[0], move[1])
                                # If user clicks neither chessboard nor back button then deselect all pieces
                                else:
                                    if i % 2 == j % 2:
                                        squareImg.clr = clrLightSquare
                                    else:
                                        squareImg.clr = clrDarkSquare
                # Perform optimal move on AI's turn (if on AI mode)
                elif currentBoard.turn == "black" and currentScreen == "ai":
                    if currentBoard.gameResult == None:
                        optimalMove = currentBoard.getOptimalMove(3, float('-inf'), float('inf'))
                        if optimalMove[0] != None:
                            currentBoard.move(optimalMove[0][0], optimalMove[0][1])
                        else:
                            print("No move available.")
                else:
                    indicatedLegalMoves = []
                    for i in range(8):
                        for j in range(8):
                            squareImg = currentBoard.guiArray[i][j]
                            # Display indicated legal moves based on selected square
                            if squareImg.clr == clrSelected:
                                for move in currentBoard.legalMoves:
                                    if move[0] == (i, j):
                                        indicatedLegalMoves.append(move)
                                for move in indicatedLegalMoves:
                                    currentBoard.guiArray[move[1]].clr = clrLegalSquare

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
                    userLookupBox.clr = clrSelected

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
                if userLookupBox.clr == clrSelected:
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
        localBoard.draw()

    # Draw AI mode
    elif currentScreen == "ai":
        display.fill(clrBlue)
        backButtonImg.draw()
        aiBoard.draw()

    # Draw stats and config screen
    elif currentScreen == "statsConf":
        display.fill(clrBlue)
        backButtonImg.draw()
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