import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells) == self.count and self.count > 0:
            return self.cells.copy()
        return set()

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count == 0:
            return self.cells.copy()
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        """

        # mark the cell as a move that has been made
        self.moves_made.add(cell)

        # mark the cell as safe
        self.mark_safe(cell)

        # add a new sentence to the AI's knowledge base based on the value of `cell` and `count`
        # Get all neighbors of the cell
        neighbors = set()
        for i in range(max(0, cell[0] - 1), min(self.height, cell[0]+2)):
            for j in range(max(0, cell[1] - 1), min(self.width, cell[1]+2)):
                if (i, j) != cell:
                    neighbors.add((i, j))

        # Remove cells that are already known to be safe or mines
        unknown_neighbours = set()
        remaining_count = count
        for neighbor in neighbors:
            if neighbor in self.mines:
                remaining_count -= 1
            elif neighbor not in self.safes:
                unknown_neighbours.add(neighbor)

        # Add the new sentence to the knowledge base
        if unknown_neighbours:
            self.knowledge.append(Sentence(unknown_neighbours, remaining_count))

        # mark any additional cells as safe or as mines
        # Keep checking for new information until no new information is found
        while True:
            new_info = False

            # Look for sentences where count = 0 (all safe) or count = length (all mines)
            safes = set()
            mines = set()

            for sentence in self.knowledge:
                safe_cells = sentence.known_safes()
                mine_cells = sentence.known_mines()

                if safe_cells:
                    safes.update(safe_cells)
                    new_info = True

                if mine_cells:
                    mines.update(mine_cells)
                    new_info = True

            # Mark any new safes or mines
            for safe in safes:
                self.mark_safe(safe)
            for mine in mines:
                self.mark_mine(mine)

            # add any new sentences to the AI's knowledge base if they can be inferred from existing knowledge
            new_sentences = []
            for s1 in self.knowledge:
                for s2 in self.knowledge:
                    if s1.cells and s2.cells and s1 != s2 and s1.cells.issubset(s2.cells):
                        new_cells = s2.cells - s1.cells
                        new_count = s2.count - s1.count
                        new_sentence = Sentence(new_cells, new_count)

            # Only add if this is actually new information
                        if new_sentence not in self.knowledge and new_sentence not in new_sentences:
                            new_sentences.append(new_sentence)
                            new_info = True

            self.knowledge.extend(new_sentences)

            # Remove any empty sentences from knowledge base
            self.knowledge = [s for s in self.knowledge if s.cells]

            # If no new information was found, break the loop
            if not new_info:
                break

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        for cell in self.safes:
            if cell not in self.moves_made:
                return cell
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        # Get all possible moves
        all_moves = set((i, j) for i in range(self.height) for j in range(self.width))

        # Remove moves that are known mines or already made
        possible_moves = all_moves - self.mines - self.moves_made
        if possible_moves:
            return possible_moves.pop()
        return None
