package game

type Intent struct {
	MoveX  int
	MoveY  int
	Action bool
}

type State struct {
	playerX int
	playerY int
	score   int
}

func NewState() *State {
	return &State{playerX: 100, playerY: 100}
}

func (s *State) Tick(intent Intent) {
	s.playerX += intent.MoveX * 2
	s.playerY += intent.MoveY * 2
	if intent.Action {
		s.score++
	}
}

type Snapshot struct {
	PlayerX int
	PlayerY int
	Score   int
}

func (s *State) Snapshot() Snapshot {
	return Snapshot{PlayerX: s.playerX, PlayerY: s.playerY, Score: s.score}
}
