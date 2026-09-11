package sample

import "context"

type Server struct {
	name string
}

func (s *Server) Start(ctx context.Context) error {
	return nil
}
