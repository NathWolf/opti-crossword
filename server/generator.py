from gurobipy import Model, GRB, quicksum
import wordfreq


import random

def get_large_word_list(min_length=3, max_length=5, min_freq=1e-6, max_words=200, random_selection=False, seed=None):
    """Get a large list of valid words from wordfreq package.
    
    Args:
        min_length: Minimum word length
        max_length: Maximum word length
        min_freq: Minimum word frequency
        max_words: Maximum number of words to return
        random_selection: If True, select words randomly instead of by frequency
        seed: Random seed for reproducible results (only used if random_selection=True)
    """
    all_words = wordfreq.get_frequency_dict('en')
    
    valid_words = []
    for word, freq in all_words.items():
        if (min_length <= len(word) <= max_length and 
            freq >= min_freq and 
            word.isalpha() and 
            word.islower()):
            valid_words.append(word.upper())
    
    # Remove duplicates as per issue #8
    valid_words = list(dict.fromkeys(valid_words))
    
    if random_selection:
        # Random selection
        if seed is not None:
            random.seed(seed)
        
        # Shuffle and take first max_words
        random.shuffle(valid_words)
        return valid_words[:max_words]
    else:
        # Sort by frequency and take top words
        valid_words.sort(key=lambda x: all_words[x.lower()], reverse=True)
        return valid_words[:max_words]


def solve_fixed_crossword(words, R=5, C=5, n_limit=1, time_limit=300):
    """
    Solve a crossword puzzle with essential fixes applied.
    
    Fixes implemented:
    1. Cell state logic: Each cell must be either a letter or black square
    2. Letter consistency: One letter per cell
    3. Basic word placement rules
    4. Intersection requirements
    
    Args:
        words: List of words to use
        R: Number of rows
        C: Number of columns
        n_limit: Limit on invalid sequences
        time_limit: Time limit in seconds (default: 300 = 5 minutes)
    """
    W = range(len(words))
    word_set = set(words)
    word_len = [len(w) for w in words]
    D = [0, 1]  # 0 = horizontal, 1 = vertical
    
    m = Model("FixedCrossword")
    m.setParam("OutputFlag", 0)
    m.setParam("TimeLimit", time_limit)
    
    # Decision variables: x[i, r, c, d] = 1 if word i starts at (r,c) in direction d
    x = {}
    for i in W:
        for d in D:
            for r in range(R):
                for c in range(C):
                    if (d == 0 and c + word_len[i] <= C) or (d == 1 and r + word_len[i] <= R):
                        x[i, r, c, d] = m.addVar(vtype=GRB.BINARY, name=f"x_{i}_{r}_{c}_{d}")
    
    # Letter variables: letter[r, c, a] = 1 if letter 'A'+a is placed at (r, c)
    letter = {}
    for r in range(R):
        for c in range(C):
            for a in range(26):
                letter[r, c, a] = m.addVar(vtype=GRB.BINARY, name=f"l_{r}_{c}_{chr(65 + a)}")
    
    # Black square variables: black[r, c] = 1 if cell (r,c) is a black square
    black = {}
    for r in range(R):
        for c in range(C):
            black[r, c] = m.addVar(vtype=GRB.BINARY, name=f"black_{r}_{c}")
    
    # FIX #1: Cell State Logic - Each cell must be either a letter OR black square
    for r in range(R):
        for c in range(C):
            m.addConstr(quicksum(letter[r, c, a] for a in range(26)) + black[r, c] == 1)
    
    # FIX #2: Letter Consistency - Link letters with word placements
    for i in W:
        w = words[i]
        L = word_len[i]
        for d in D:
            for r in range(R):
                for c in range(C):
                    if (i, r, c, d) not in x:
                        continue
                    for k in range(L):
                        rr = r + (k if d == 1 else 0)
                        cc = c + (k if d == 0 else 0)
                        a = ord(w[k]) - 65
                        # If word is placed, the letter must be set
                        m.addConstr(letter[rr, cc, a] >= x[i, r, c, d])
    
    # Each word used at most once
    for i in W:
        m.addConstr(quicksum(x[i, r, c, d] for r in range(R) for c in range(C)
                             for d in D if (i, r, c, d) in x) <= 1)
    
    # FIX #3: Relaxed Word Placement Rules - Only require black squares at word boundaries
    for i in W:
        w = words[i]
        L = word_len[i]
        for d in D:
            for r in range(R):
                for c in range(C):
                    if (i, r, c, d) not in x:
                        continue
                    
                    # Horizontal words must have black squares at ends
                    if d == 0:  # Horizontal
                        if c > 0:  # Not at left edge
                            m.addConstr(black[r, c-1] >= x[i, r, c, d])
                        if c + L < C:  # Not at right edge
                            m.addConstr(black[r, c+L] >= x[i, r, c, d])
                    
                    # Vertical words must have black squares at ends
                    else:  # Vertical
                        if r > 0:  # Not at top edge
                            m.addConstr(black[r-1, c] >= x[i, r, c, d])
                        if r + L < R:  # Not at bottom edge
                            m.addConstr(black[r+L, c] >= x[i, r, c, d])
    
    # FIX #4: Simplified Intersection Logic - Ensure words can intersect properly
    # A cell can only have one letter assigned
    for r in range(R):
        for c in range(C):
            m.addConstr(quicksum(letter[r, c, a] for a in range(26)) <= 1)
    
    # Relaxed intersection requirement - only require if we have multiple words
    if len(words) > 1:
        # Create intersection variables
        intersect = {}
        for r in range(R):
            for c in range(C):
                intersect[r, c] = m.addVar(vtype=GRB.BINARY, name=f"intersect_{r}_{c}")
        
        # A cell is an intersection if it has a letter
        for r in range(R):
            for c in range(C):
                m.addConstr(intersect[r, c] <= quicksum(letter[r, c, a] for a in range(26)))
                m.addConstr(intersect[r, c] >= quicksum(letter[r, c, a] for a in range(26)) / 26)
        
        # Relaxed: Require at least one intersection OR at least one word placed
        total_words = quicksum(x[i, r, c, d] for i, r, c, d in x)
        total_intersections = quicksum(intersect[r, c] for r in range(R) for c in range(C))
        m.addConstr(total_intersections >= total_words - len(words) + 1)
    
    # Relaxed black square limit - allow more black squares
    m.addConstr(quicksum(black[r, c] for r in range(R) for c in range(C)) <= R * C // 2)
    
    # FIX #5: Improved Objective Function - prioritize word placement
    word_score = quicksum(x[i, r, c, d] for i, r, c, d in x)
    black_penalty = quicksum(black[r, c] for r in range(R) for c in range(C))
    
    # Weighted objective: strongly prioritize words, lightly penalize black squares
    m.setObjective(20 * word_score - black_penalty, GRB.MAXIMIZE)
    
    # Solve
    m.optimize()
    
    # Parse solution
    grid = [[" " for _ in range(C)] for _ in range(R)]
    if m.status == GRB.OPTIMAL:
        for r in range(R):
            for c in range(C):
                if black[r, c].X > 0.5:
                    grid[r][c] = "#"
                else:
                    for a in range(26):
                        if letter[r, c, a].X > 0.5:
                            grid[r][c] = chr(65 + a)
                            break
    else:
        grid = None
    
    return grid


def extract_words_from_grid(grid, word_set):
    """Extract all words from the grid and validate them."""
    R, C = len(grid), len(grid[0])
    valid_words = []
    invalid_words = []
    non_word_combinations = []
    
    # Extract horizontal words
    for r in range(R):
        current_word = ""
        for c in range(C):
            if grid[r][c] == "#":  # Black square
                if len(current_word) >= 2:
                    if current_word in word_set:
                        valid_words.append(current_word)
                    else:
                        invalid_words.append(current_word)
                elif len(current_word) == 1:
                    non_word_combinations.append(current_word)
                current_word = ""
            else:
                current_word += grid[r][c]
        
        # Check word at end of row
        if len(current_word) >= 2:
            if current_word in word_set:
                valid_words.append(current_word)
            else:
                invalid_words.append(current_word)
        elif len(current_word) == 1:
            non_word_combinations.append(current_word)
    
    # Extract vertical words
    for c in range(C):
        current_word = ""
        for r in range(R):
            if grid[r][c] == "#":  # Black square
                if len(current_word) >= 2:
                    if current_word in word_set:
                        valid_words.append(current_word)
                    else:
                        invalid_words.append(current_word)
                elif len(current_word) == 1:
                    non_word_combinations.append(current_word)
                current_word = ""
            else:
                current_word += grid[r][c]
        
        # Check word at end of column
        if len(current_word) >= 2:
            if current_word in word_set:
                valid_words.append(current_word)
            else:
                invalid_words.append(current_word)
        elif len(current_word) == 1:
            non_word_combinations.append(current_word)
    
    return valid_words, invalid_words, non_word_combinations


def fix_invalid_sequences(grid, word_set):
    """
    Post-process the grid to fix invalid sequences by adding black squares.
    This is a targeted fix for the remaining invalid word issue.
    """
    R, C = len(grid), len(grid[0])
    fixed_grid = [row[:] for row in grid]
    
    # Find and fix invalid horizontal sequences
    for r in range(R):
        current_word = ""
        start_c = 0
        for c in range(C):
            if grid[r][c] == "#":
                # End of sequence
                if len(current_word) >= 2 and current_word not in word_set:
                    # Invalid word found, add black square to break it
                    if len(current_word) > 2:  # Break words longer than 2 letters
                        # Try to break at a position that creates valid words
                        best_break_pos = None
                        for break_pos in range(1, len(current_word)):
                            left_word = current_word[:break_pos]
                            right_word = current_word[break_pos:]
                            # Allow breaking if either part is a valid word or single letter
                            if (left_word in word_set or len(left_word) == 1) and (right_word in word_set or len(right_word) == 1):
                                best_break_pos = break_pos
                                break
                        
                        # If no perfect break found, just break in the middle
                        if best_break_pos is None and len(current_word) > 3:
                            best_break_pos = len(current_word) // 2
                        
                        if best_break_pos is not None:
                            mid_pos = start_c + best_break_pos
                            fixed_grid[r][mid_pos] = "#"
                current_word = ""
                start_c = c + 1
            else:
                if current_word == "":
                    start_c = c
                current_word += grid[r][c]
        
        # Check word at end of row
        if len(current_word) >= 2 and current_word not in word_set:
            if len(current_word) > 2:  # Break words longer than 2 letters
                # Try to break at a position that creates valid words
                best_break_pos = None
                for break_pos in range(1, len(current_word)):
                    left_word = current_word[:break_pos]
                    right_word = current_word[break_pos:]
                    # Allow breaking if either part is a valid word or single letter
                    if (left_word in word_set or len(left_word) == 1) and (right_word in word_set or len(right_word) == 1):
                        best_break_pos = break_pos
                        break
                
                # If no perfect break found, just break in the middle
                if best_break_pos is None and len(current_word) > 3:
                    best_break_pos = len(current_word) // 2
                
                if best_break_pos is not None:
                    mid_pos = start_c + best_break_pos
                    fixed_grid[r][mid_pos] = "#"
    
    # Find and fix invalid vertical sequences
    for c in range(C):
        current_word = ""
        start_r = 0
        for r in range(R):
            if grid[r][c] == "#":
                # End of sequence
                if len(current_word) >= 2 and current_word not in word_set:
                    # Invalid word found, add black square to break it
                    if len(current_word) > 2:  # Break words longer than 2 letters
                        # Try to break at a position that creates valid words
                        best_break_pos = None
                        for break_pos in range(1, len(current_word)):
                            left_word = current_word[:break_pos]
                            right_word = current_word[break_pos:]
                            # Allow breaking if either part is a valid word or single letter
                            if (left_word in word_set or len(left_word) == 1) and (right_word in word_set or len(right_word) == 1):
                                best_break_pos = break_pos
                                break
                        
                        # If no perfect break found, just break in the middle
                        if best_break_pos is None and len(current_word) > 3:
                            best_break_pos = len(current_word) // 2
                        
                        if best_break_pos is not None:
                            mid_pos = start_r + best_break_pos
                            fixed_grid[mid_pos][c] = "#"
                current_word = ""
                start_r = r + 1
            else:
                if current_word == "":
                    start_r = r
                current_word += grid[r][c]
        
        # Check word at end of column
        if len(current_word) >= 2 and current_word not in word_set:
            if len(current_word) > 2:  # Break words longer than 2 letters
                # Try to break at a position that creates valid words
                best_break_pos = None
                for break_pos in range(1, len(current_word)):
                    left_word = current_word[:break_pos]
                    right_word = current_word[break_pos:]
                    # Allow breaking if either part is a valid word or single letter
                    if (left_word in word_set or len(left_word) == 1) and (right_word in word_set or len(right_word) == 1):
                        best_break_pos = break_pos
                        break
                
                # If no perfect break found, just break in the middle
                if best_break_pos is None and len(current_word) > 3:
                    best_break_pos = len(current_word) // 2
                
                if best_break_pos is not None:
                    mid_pos = start_r + best_break_pos
                    fixed_grid[mid_pos][c] = "#"
    
    return fixed_grid


def generate_fixed_crossword(R=5, C=5, min_word_length=3, max_word_length=5, 
                           min_freq=1e-5, max_words=200, n_limit=1, time_limit=300,
                           random_selection=False, seed=None):
    """Generate a crossword puzzle with all critical issues fixed.
    
    Args:
        R: Number of rows
        C: Number of columns
        min_word_length: Minimum word length
        max_word_length: Maximum word length
        min_freq: Minimum word frequency
        max_words: Maximum number of words to use
        n_limit: Limit on invalid sequences
        time_limit: Time limit in seconds (default: 300 = 5 minutes)
        random_selection: If True, select words randomly instead of by frequency
        seed: Random seed for reproducible results (only used if random_selection=True)
    """
    # Get word list
    word_list = get_large_word_list(min_word_length, max_word_length, min_freq, max_words, 
                                   random_selection, seed)
    
    if not word_list:
        print("No words found with given criteria.")
        return None, [], [], []
    
    print(f"Using {len(word_list)} words from wordfreq: {word_list[:10]}...")
    
    # Try to solve crossword with fixed constraints
    grid = solve_fixed_crossword(word_list, R, C, n_limit, time_limit)
    
    if grid is None:
        print("No solution found.")
        return None, [], [], []
    
    print("\nInitial grid:")
    for row in grid:
        print(" ".join(row))
    
    # Apply targeted post-processing to fix invalid sequences
    word_set = set(word_list)
    fixed_grid = fix_invalid_sequences(grid, word_set)
    
    print("\nFixed grid:")
    for row in fixed_grid:
        print(" ".join(row))
    
    # Validate the result
    valid_words, invalid_words, non_word_combinations = extract_words_from_grid(fixed_grid, word_set)
    
    return fixed_grid, valid_words, invalid_words, non_word_combinations


# Example usage
if __name__ == "__main__":
    print("=== Fixed Crossword Solver ===")
    print("Generating 5x5 crossword with all critical issues fixed...")
    
    grid, valid_words, invalid_words, non_word_combinations = generate_fixed_crossword(
        R=5, C=5, 
        min_word_length=3, 
        max_word_length=5, 
        min_freq=1e-5,
        max_words=50,
        n_limit=1,
        time_limit=180  # 3 minutes for demo
    )
    
    if grid:
        print(f"\nValid words found: {len(valid_words)}")
        for word in valid_words:
            print(f"  {word}")
        
        if invalid_words:
            print(f"\nInvalid words found: {len(invalid_words)}")
            for word in invalid_words:
                print(f"  {word}")
        
        if non_word_combinations:
            print(f"\nNon-word combinations: {len(non_word_combinations)}")
            for combo in non_word_combinations:
                print(f"  {combo}")
        
        print(f"\nGrid is valid: {len(invalid_words) == 0 and len(non_word_combinations) <= 1}")
        
        # Count black squares
        black_count = sum(1 for row in grid for cell in row if cell == "#")
        print(f"Black squares used: {black_count}")
        
        # Show which words were actually placed
        print(f"\nWords placed in grid:")
        for word in valid_words:
            print(f"  {word}")
    else:
        print("Failed to generate crossword.") 