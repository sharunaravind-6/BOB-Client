// client/ui/static/main.js
document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('runMatchBtn');
    const resultDisplay = document.getElementById('resultDisplay');
    const canvas = document.getElementById('tronCanvas');
    const ctx = canvas.getContext('2d');
    let animationInterval;
    let pollingInterval;

    runBtn.addEventListener('click', startMatch);

    async function startMatch() {
        clearInterval(animationInterval);
        clearInterval(pollingInterval);
        resultDisplay.textContent = 'Requesting match...';
        runBtn.disabled = true;

        const payload = {
            language: document.getElementById('language').value,
            bot_path: document.getElementById('botPath').value,
            team_name: document.getElementById('teamName').value
        };

        try {
            const response = await fetch('/run-match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (data.status === 'started') {
                resultDisplay.textContent = 'Match started... Waiting for result.';
                pollForResult(data.match_id);
            } else {
                throw new Error(data.error || 'Failed to start match.');
            }
        } catch (error) {
            resultDisplay.textContent = `Error: ${error.message}`;
            runBtn.disabled = false;
        }
    }

    function pollForResult(matchId) {
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/match-status/${matchId}`);
                const data = await response.json();

                if (data.status === 'complete') {
                    clearInterval(pollingInterval);
                    resultDisplay.textContent = `Result: ${data.log.result.winner}`;
                    animateMatch(data.log.frames);
                    runBtn.disabled = false;
                } else if (data.status === 'error') {
                    clearInterval(pollingInterval);
                    resultDisplay.textContent = `Error: ${data.log.error}`;
                    console.error('Raw error output:', data.log.raw_output);
                    runBtn.disabled = false;
                }
                // If status is "running", do nothing and wait for the next poll.
            } catch (error) {
                clearInterval(pollingInterval);
                resultDisplay.textContent = `Polling Error: ${error.message}`;
                runBtn.disabled = false;
            }
        }, 2000); // Poll every 2 seconds
    }

    function animateMatch(frames) {
        let frameIndex = 0;
        const boardConfig = frames[0].board;
        const cellWidth = canvas.width / boardConfig.width;
        const cellHeight = canvas.height / boardConfig.height;

        animationInterval = setInterval(() => {
            if (frameIndex >= frames.length) {
                clearInterval(animationInterval);
                return;
            }
            drawFrame(frames[frameIndex], cellWidth, cellHeight);
            frameIndex++;
        }, 100);
    }

    function drawFrame(frame, cellW, cellH) {
        ctx.fillStyle = '#1e2228';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#61afef'; // P1 Blue
        frame.p1.body.forEach(part => ctx.fillRect(part.x * cellW, part.y * cellH, cellW, cellH));
        ctx.fillStyle = '#e06c75'; // P2 Red
        frame.p2.body.forEach(part => ctx.fillRect(part.x * cellW, part.y * cellH, cellW, cellH));
        if (frame.p1.alive) {
            ctx.fillStyle = '#98c379'; // P1 Head Green
            ctx.fillRect(frame.p1.head.x * cellW, frame.p1.head.y * cellH, cellW, cellH);
        }
        if (frame.p2.alive) {
            ctx.fillStyle = '#e5c07b'; // P2 Head Yellow
            ctx.fillRect(frame.p2.head.x * cellW, frame.p2.head.y * cellH, cellW, cellH);
        }
    }
});