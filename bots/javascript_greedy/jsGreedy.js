const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Preferred move order
const moveOrder = ["UP", "RIGHT", "DOWN", "LEFT"];
const moves = { "UP": {dx:0, dy:-1}, "DOWN": {dx:0, dy:1}, "LEFT": {dx:-1, dy:0}, "RIGHT": {dx:1, dy:0} };

rl.on('line', (line) => {
    try {
        const state = JSON.parse(line);
        const { board, you } = state;
        const { width, height, grid } = board;
        const { head } = you;
        const { x: hx, y: hy } = head;

        let chosenMove = moveOrder[0]; // Default move if trapped

        // Find the first safe move in the preferred order
        for (const move of moveOrder) {
            const { dx, dy } = moves[move];
            const nx = hx + dx;
            const ny = hy + dy;

            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                if (grid[ny][nx] === '0') {
                    chosenMove = move;
                    break; // Found a safe move, stop searching
                }
            }
        }
        
        // Send the move back to the game engine
        const response = { move: chosenMove };
        console.log(JSON.stringify(response));

    } catch (e) {
        // If JSON is invalid or any other error, do nothing and let the referee handle it.
    }
});