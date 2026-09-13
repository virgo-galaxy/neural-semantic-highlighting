package pipeline

type Source interface {
	Next() (string, bool)
}

type Handler struct {
	Source Source
	Name   string
}

func (h *Handler) Read() string {
	value, ok := h.Source.Next()
	if !ok {
		return h.Name
	}
	return value
}

func Consume(handler *Handler) string {
	return handler.Read()
}
