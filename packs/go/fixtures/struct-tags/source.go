package metadata

type Record struct {
	ID      int64  `json:"id" gorm:"primaryKey;column:id"`
	Name    string `json:"name,omitempty" binding:"required" validate:"min=1,max=64"`
	Email   string `xml:"email,omitempty" yaml:"email" db:"email"`
	Note    string "json:\"note,omitempty\" custom:\"display\""
	Details struct {
		Enabled bool `json:"enabled"`
	} `json:"details"`
}
