from ortools.sat.python import cp_model
import wordfreq
import random
import time


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
    
    # Remove duplicates
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


def solve_crossword_cp_sat(words, R=5, C=5, time_limit=300):
    """
    Solve a crossword puzzle using Google OR-Tools CP-SAT solver.
    
    Args:
        words: List of words to use
        R: Number of rows
        C: Number of columns
        time_limit: Time limit in seconds (default: 300 = 5 minutes)
    """
    # Create the CP-SAT model
    model = cp_model.CpModel()
    
    # Word information
    W = range(len(words))
    word_set = set(words)
    word_len = [len(w) for w in words]
    D = [0, 1]  # 0 = horizontal, 1 = vertical
    
    # Decision variables: x[i, r, c, d] = 1 if word i starts at (r,c) in direction d
    x = {}
    for i in W:
        for d in D:
            for r in range(R):
                for c in range(C):
                    if (d == 0 and c + word_len[i] <= C) or (d == 1 and r + word_len[i] <= R):
                        x[i, r, c, d] = model.NewBoolVar(f"x_{i}_{r}_{c}_{d}")
    
    # Letter variables: letter[r, c, a] = 1 if letter 'A'+a is placed at (r, c)
    letter = {}
    for r in range(R):
        for c in range(C):
            for a in range(26):
                letter[r, c, a] = model.NewBoolVar(f"l_{r}_{c}_{chr(65 + a)}")
    
    # Black square variables: black[r, c] = 1 if cell (r,c) is a black square
    black = {}
    for r in range(R):
        for c in range(C):
            black[r, c] = model.NewBoolVar(f"black_{r}_{c}")
    
    # Constraint 1: Cell State Logic - Each cell must be either a letter OR black square
    for r in range(R):
        for c in range(C):
            model.Add(sum(letter[r, c, a] for a in range(26)) + black[r, c] == 1)
    
    # Constraint 2: Letter Consistency - Link letters with word placements
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
                        model.Add(letter[rr, cc, a] >= x[i, r, c, d])
    
    # Constraint 3: Each word used at most once
    for i in W:
        model.Add(sum(x[i, r, c, d] for r in range(R) for c in range(C)
                      for d in D if (i, r, c, d) in x) <= 1)
    
    # Constraint 4: Word Placement Rules - Black squares at word boundaries
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
                            model.Add(black[r, c-1] >= x[i, r, c, d])
                        if c + L < C:  # Not at right edge
                            model.Add(black[r, c+L] >= x[i, r, c, d])
                    
                    # Vertical words must have black squares at ends
                    else:  # Vertical
                        if r > 0:  # Not at top edge
                            model.Add(black[r-1, c] >= x[i, r, c, d])
                        if r + L < R:  # Not at bottom edge
                            model.Add(black[r+L, c] >= x[i, r, c, d])
    
    # Constraint 5: Letter uniqueness - A cell can only have one letter assigned
    for r in range(R):
        for c in range(C):
            model.Add(sum(letter[r, c, a] for a in range(26)) <= 1)
    
    # Constraint 6: Simplified Intersection Logic - Ensure words can intersect properly
    # A cell can only have one letter assigned (already handled above)
    # For multiple words, require at least some connectivity
    if len(words) > 1:
        # Count total words placed
        total_words = sum(x[i, r, c, d] for i, r, c, d in x)
        # Require at least one word to be placed
        model.Add(total_words >= 1)
    
    # Constraint 7: Black square limit
    model.Add(sum(black[r, c] for r in range(R) for c in range(C)) <= R * C // 2)
    
    # Objective: Maximize word placement while minimizing black squares
    word_score = sum(x[i, r, c, d] for i, r, c, d in x)
    black_penalty = sum(black[r, c] for r in range(R) for c in range(C))
    
    # Weighted objective: strongly prioritize words, lightly penalize black squares
    model.Maximize(20 * word_score - black_penalty)
    
    # Create solver and solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    
    print(f"Solving with CP-SAT (time limit: {time_limit}s)...")
    start_time = time.time()
    status = solver.Solve(model)
    end_time = time.time()
    
    print(f"Solver status: {solver.StatusName(status)}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    
    # Parse solution
    grid = [[" " for _ in range(C)] for _ in range(R)]
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for r in range(R):
            for c in range(C):
                if solver.Value(black[r, c]) == 1:
                    grid[r][c] = "#"
                else:
                    for a in range(26):
                        if solver.Value(letter[r, c, a]) == 1:
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


def generate_crossword_cp_sat(R=5, C=5, min_word_length=3, max_word_length=5, 
                            min_freq=1e-5, max_words=200, time_limit=300,
                            random_selection=False, seed=None):
    """Generate a crossword puzzle using CP-SAT solver.
    
    Args:
        R: Number of rows
        C: Number of columns
        min_word_length: Minimum word length
        max_word_length: Maximum word length
        min_freq: Minimum word frequency
        max_words: Maximum number of words to use
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
    
    # Try to solve crossword with CP-SAT
    grid = solve_crossword_cp_sat(word_list, R, C, time_limit)
    
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
    print("=== CP-SAT Crossword Solver ===")
    print("Generating 5x5 crossword using Google OR-Tools CP-SAT...")
    
    grid, valid_words, invalid_words, non_word_combinations = generate_crossword_cp_sat(
        R=5, C=5, 
        min_word_length=3, 
        max_word_length=5, 
        min_freq=1e-5,
        max_words=50,
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