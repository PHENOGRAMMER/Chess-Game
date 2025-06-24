import pygame
import ChessEngine
import time

BOARD_WIDTH = BOARD_HEIGHT = 520
EXTRA_SPACE = 120
MOVE_LOG_PANEL_WIDTH = 240
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 60
IMAGES = {}
colors = [pygame.Color("#F0D9B5"), pygame.Color("#B58863")]


def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        try:
            img = pygame.image.load("images/" + piece + ".png")
            IMAGES[piece] = pygame.transform.scale(img, (SQ_SIZE - 4, SQ_SIZE - 4))
        except pygame.error:
            surface = pygame.Surface((SQ_SIZE - 4, SQ_SIZE - 4))
            color = pygame.Color("lightgray") if piece[0] == 'w' else pygame.Color("darkgray")
            surface.fill(color)
            font = pygame.font.SysFont("Arial", 24, True)
            text = font.render(piece[1], True, pygame.Color("black"))
            text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
            surface.blit(text, text_rect)
            IMAGES[piece] = surface


def askPromotionChoice(screen):
    font = pygame.font.SysFont("Arial", 20, True)
    options = ["Q", "R", "B", "N"]
    promptRect = pygame.Rect(BOARD_WIDTH // 2 - 100, BOARD_HEIGHT // 2 - 50, 200, 100)
    pygame.draw.rect(screen, pygame.Color("gray"), promptRect)
    prompt = font.render("Promote to:", True, pygame.Color("white"))
    screen.blit(prompt, (promptRect.x + 40, promptRect.y + 10))

    buttonRects = []
    for i, piece in enumerate(options):
        btn = pygame.Rect(promptRect.x + 10 + i * 45, promptRect.y + 50, 40, 30)
        buttonRects.append((btn, piece))
        pygame.draw.rect(screen, pygame.Color("black"), btn)
        text = font.render(piece, True, pygame.Color("white"))
        screen.blit(text, (btn.x + 12, btn.y + 5))

    pygame.display.flip()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for rect, choice in buttonRects:
                    if rect.collidepoint(pos):
                        return choice


def main():
    pygame.init()
    global screen
    screen = pygame.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT + EXTRA_SPACE))
    pygame.display.set_caption("Chess Game")
    clock = pygame.time.Clock()
    loadImages()

    gameOver = False
    whiteTime = 300
    blackTime = 300
    lastTick = time.time()

    gs = ChessEngine.GameState()
    gs.flipBoard = False
    validMoves = gs.getValidMoves()
    moveMade = False
    running = True
    sqSelected = ()
    playerClicks = []
    moveLogFont = pygame.font.SysFont("Consolas", 18, True)
    resultFont = pygame.font.SysFont("Helvetica", 32, True, False)
    winnerText = ""

    playerOne = True
    playerTwo = True

    while running:
        currentTime = time.time()
        elapsed = currentTime - lastTick
        lastTick = currentTime

        if not gameOver:
            if gs.whiteToMove:
                whiteTime -= elapsed
            else:
                blackTime -= elapsed
            whiteTime = max(0, whiteTime)
            blackTime = max(0, blackTime)
            if whiteTime <= 0:
                gameOver = True
                winnerText = "Black wins on time!"
            elif blackTime <= 0:
                gameOver = True
                winnerText = "White wins on time!"

        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif not gs.checkMate and not gs.staleMate and humanTurn and not gameOver:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    location = pygame.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE

                    if gs.flipBoard:
                        row = 7 - row
                        col = 7 - col

                    if col >= DIMENSION or row >= DIMENSION:
                        continue

                    if sqSelected == (row, col):
                        sqSelected = ()
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)

                    if len(playerClicks) == 2:
                        start = playerClicks[0]
                        end = playerClicks[1]
                        piece = gs.board[start[0]][start[1]]
                        promotionChoice = None
                        isPromotion = (piece == 'wp' and end[0] == 0) or (piece == 'bp' and end[0] == 7)
                        if isPromotion:
                            promotionChoice = askPromotionChoice(screen)
                        move = ChessEngine.Move(start, end, gs.board, promotionChoice=promotionChoice)
                        for validMove in validMoves:
                            if move == validMove:
                                gs.makeMove(validMove)
                                gs.flipBoard = not gs.flipBoard
                                animatedMove(validMove, screen, gs.board, clock, gs.flipBoard)
                                moveMade = True
                                sqSelected = ()
                                playerClicks = []
                                break
                        if not moveMade:
                            playerClicks = [sqSelected]

                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_z:
                        gs.undoMove()
                        gs.flipBoard = not gs.flipBoard
                        validMoves = gs.getValidMoves()
                        moveMade = False
                        sqSelected = ()
                        playerClicks = []

        # if not gs.checkMate and not gs.staleMate and not humanTurn and not gameOver:
        #     AIMove = ChessEngine.findRandomMoves(validMoves)
        #     if AIMove:
        #         gs.makeMove(AIMove)
        #         gs.flipBoard = not gs.flipBoard
        #         animatedMove(AIMove, screen, gs.board, clock, gs.flipBoard)
        #         moveMade = True

        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False
            if not gameOver:
                gs.flipBoard = not gs.flipBoard

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)
        drawClock(screen, whiteTime, blackTime)
        if gameOver:
            drawEndGameText(screen, winnerText, resultFont)
        elif gs.checkMate:
            drawEndGameText(screen, "Black wins by checkmate" if gs.whiteToMove else "White wins by checkmate",
                            resultFont)
        elif gs.staleMate:
            drawEndGameText(screen, "Draw by stalemate", resultFont)

        clock.tick(MAX_FPS)
        pygame.display.flip()

    pygame.quit()


def drawGameState(screen, gs, validMoves, sqSelected, font):
    drawBoard(screen, gs.flipBoard)
    highlightSquares(screen, gs, validMoves, sqSelected, gs.flipBoard)
    drawPieces(screen, gs.board, gs.flipBoard)
    drawMoveLog(screen, gs, font)


def drawBoard(screen, flip=False):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            row = 7 - r if flip else r
            col = 7 - c if flip else c
            color = colors[(row + col) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(screen, board, flip=False):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            row = 7 - r if flip else r
            col = 7 - c if flip else c
            piece = board[row][col]
            if piece != "--":
                img = IMAGES[piece]
                x = c * SQ_SIZE + (SQ_SIZE - img.get_width()) // 2
                y = r * SQ_SIZE + (SQ_SIZE - img.get_height()) // 2
                screen.blit(img, (x, y))


def drawClock(screen, whiteTime, blackTime):
    font = pygame.font.SysFont("Consolas", 22, True)

    def formatTime(t):
        minutes = int(t) // 60
        seconds = int(t) % 60
        return f"{minutes:02d}:{seconds:02d}"

    whiteClock = font.render(f"White: {formatTime(whiteTime)}", True, pygame.Color("white"))
    blackClock = font.render(f"Black: {formatTime(blackTime)}", True, pygame.Color("white"))

    pygame.draw.rect(screen, pygame.Color("black"), pygame.Rect(0, BOARD_HEIGHT, BOARD_WIDTH, EXTRA_SPACE))
    screen.blit(whiteClock, (10, BOARD_HEIGHT + 10))
    screen.blit(blackClock, (BOARD_WIDTH - 160, BOARD_HEIGHT + 10))



def highlightSquares(screen, gs, validMoves, sqSelected, flip=False):
    if sqSelected != ():
        r, c = sqSelected
        row = 7 - r if flip else r
        col = 7 - c if flip else c
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            s = pygame.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(pygame.Color('blue'))
            screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
            s.fill(pygame.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    endRow = 7 - move.endRow if flip else move.endRow
                    endCol = 7 - move.endCol if flip else move.endCol
                    screen.blit(s, (endCol * SQ_SIZE, endRow * SQ_SIZE))


def drawMoveLog(screen, gs, font):
    moveLogRect = pygame.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    pygame.draw.rect(screen, pygame.Color('black'), moveLogRect)
    moveLog = gs.moveLog
    padding = 5
    lineSpacing = 20
    textY = padding
    for i in range(0, len(moveLog), 2):
        whiteMove = moveLog[i].getChessNotation()
        blackMove = moveLog[i + 1].getChessNotation() if i + 1 < len(moveLog) else ""
        moveText = f"{i // 2 + 1}. {whiteMove}   {blackMove}"
        textObject = font.render(moveText, True, pygame.Color('white'))
        screen.blit(textObject, (BOARD_WIDTH + padding, textY))
        textY += lineSpacing
        if textY > MOVE_LOG_PANEL_HEIGHT - lineSpacing:
            break


def drawEndGameText(screen, text, font):
    textObject = font.render(text, True, pygame.Color('Red'))
    textLocation = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
        BOARD_WIDTH // 2 - textObject.get_width() // 2,
        BOARD_HEIGHT // 2 - textObject.get_height() // 2
    )
    screen.blit(textObject, textLocation)


def animatedMove(move, screen, board, clock, flip=False):
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 5
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare

    for frame in range(frameCount + 1):
        r = move.startRow + dR * frame / frameCount
        c = move.startCol + dC * frame / frameCount

        drawBoard(screen, flip)
        drawPieces(screen, board, flip)

        drawR = 7 - r if flip else r
        drawC = 7 - c if flip else c
        endRow = 7 - move.endRow if flip else move.endRow
        endCol = 7 - move.endCol if flip else move.endCol

        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = pygame.Rect(endCol * SQ_SIZE, endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        pygame.draw.rect(screen, color, endSquare)

        if move.pieceCaptured != "--":
            screen.blit(IMAGES[move.pieceCaptured], endSquare)

        pieceImage = IMAGES[move.pieceMoved]
        screen.blit(pieceImage, pygame.Rect(drawC * SQ_SIZE, drawR * SQ_SIZE, SQ_SIZE, SQ_SIZE))

        pygame.display.flip()
        clock.tick(MAX_FPS)


if __name__ == "__main__":
    main()
