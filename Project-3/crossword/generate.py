import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            # Create a copy of the domain to avoid midfying it during iteration
            domain = self.domains[var].copy()
            # Check each woed in the domain
            for word in domain:
                # If the word length doesn't match the variable length, remove it
                if len(word) != var.length:
                    self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False

        # Get the overlap between the variables x and y
        overlap = self.crossword.overlaps[x, y]

        # If there's no overlap, no revision needed
        if overlap is None:
            return False

        # Get the indices where the variables overlap
        i, j = overlap

        # Check each word in x's domain
        # Make a copy to avoid modifying during iteration
        x_domain = self.domains[x].copy()

        for x_word in x_domain:
            # Check if there exists any word in y's domain that could work with x_word
            has_valid_y = False
            for y_word in self.domains[y]:
                if x_word[i] == y_word[j]:
                    has_valid_y = True
                    break
            
            # If no valid y word exists, remove x_word from x's domain
            if not has_valid_y:
                self.domains[x].remove(x_word)
                revised = True

        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # If arcs is None, start with all possible arcs
        if arcs is None:
            arcs = []
            for v1 in self.crossword.variables:
                for v2 in self.crossword.neighbors(v1):
                    arcs.append((v1, v2))

        # Create a queue of arcs to process
        queue = arcs.copy()

        # Keep enforcing arc consistency until no more changes
        while queue:
            x, y = queue.pop(0)

            # If we revise the domain of x
            if self.revise(x, y):
                # If x's domain is empty, this puzzel is unsolvable
                if len(self.domains[x]) == 0:
                    return False
                
                # Add all neighbors of x (except y) to queue
                for neighbor in self.crossword.neighbors(x) - {y}:
                    queue.append((neighbor, x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Check if every variable in the crossword has a value assigned
        return all(var in assignment for var in self.crossword.variables)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Check if all values are distinct
        used_words = set()
        for var in assignment:
            word = assignment[var]

            # Check if word has correct length
            if len(word) != var.length:
                return False
            
            # Check if word is already used
            if word in used_words:
                return False
            used_words.add(word)

            # Check conflicts between neighboring variables
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    # Get overlap point
                    overlap = self.crossword.overlaps[var, neighbor]
                    if overlap:
                        i, j = overlap
                        # Check if characters at overlap point match
                        if word[i] != assignment[neighbor][j]:
                            return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Dictionary to store how many values each domain value rules out
        values_ruled_out = {}

        # For each possible value in var's domain
        for value in self.domains[var]:
            ruled_out = 0

            # Check impact on each unassigned neighbor
            for neighbor in self.crossword.neighbors(var):
                # Skip neighbors that are already assigned
                if neighbor in assignment:
                    continue

                # Get the overlap between var and neighbor
                overlap = self.crossword.overlaps[var, neighbor]
                if overlap is None:
                    continue

                i, j = overlap

                # Check how many values in neighbor's domain would be ruled out
                for neighbor_value in self.domains[neighbor]:
                    if value[i] != neighbor_value[j]:
                        ruled_out += 1
            
            values_ruled_out[value] = ruled_out

        return sorted(self.domains[var], key=lambda x: values_ruled_out[x])             

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned = []
        for var in self.crossword.variables:
            if var not in assignment:
                # Get number of remaining values and degree for this variable
                remaining_values = len(self.domains[var])
                degree = len(self.crossword.neighbors(var))
                unassigned.append((var, remaining_values, degree))
        
        # Sort by remaining values (ascending) and degree (descending)
        # The negative sign before degree makes it sort in descending order
        return min(unassigned, key=lambda x: (x[1], -x[2]))[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # If assignment complete, return it
        if self.assignment_complete(assignment):
            return assignment
            
        # Select an unassigned variable using our heuristics
        var = self.select_unassigned_variable(assignment)
        
        # Try each value in the domain of the variable
        for value in self.order_domain_values(var, assignment):
            # Create a new assignment with this value
            new_assignment = assignment.copy()
            new_assignment[var] = value
            
            # Check if the assignment is consistent
            if self.consistent(new_assignment):
                # If consistent, add to assignment and propagate constraints
                assignment[var] = value
                
                # Maintain arc consistency
                arcs = [(neighbor, var) for neighbor in self.crossword.neighbors(var)
                        if neighbor not in assignment]
                if self.ac3(arcs):
                    # Recursively try to complete the assignment
                    result = self.backtrack(assignment)
                    if result is not None:
                        return result
                
                # If we get here, we need to backtrack
                assignment.pop(var)
                
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
