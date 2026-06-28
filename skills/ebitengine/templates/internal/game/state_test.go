package game

import "testing"

func TestPlayerMovesRight(t *testing.T) {
	state := NewState()
	state.Tick(Intent{MoveX: 1})

	if got, want := state.Snapshot().PlayerX, 102; got != want {
		t.Fatalf("PlayerX = %d, want %d", got, want)
	}
}

func TestActionIncreasesScore(t *testing.T) {
	state := NewState()
	state.Tick(Intent{Action: true})

	if got, want := state.Snapshot().Score, 1; got != want {
		t.Fatalf("Score = %d, want %d", got, want)
	}
}
