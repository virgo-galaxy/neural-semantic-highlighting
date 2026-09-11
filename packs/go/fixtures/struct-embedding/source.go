package embedding

type Address struct {
	City string
}

func (a Address) Format() string { return a.City }

type Formatter interface {
	Format() string
}

type NamedFormatter interface {
	Formatter
	Name() string
}

type Record struct {
	*Address
	Extra struct {
		Code int
	}
}

func Read(record Record) string {
	_ = record.City
	_ = record.Extra.Code
	_ = record.Format
	_ = (*Record).Format
	return record.Format()
}
