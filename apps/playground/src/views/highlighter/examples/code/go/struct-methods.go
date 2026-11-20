package account

type Profile struct {
	Name   string
	Active bool
}

func (p *Profile) Rename(name string) {
	p.Name = name
}

func (p Profile) DisplayName() string {
	return p.Name
}

func Update(profile *Profile, name string) string {
	profile.Rename(name)
	if profile.Active {
		return profile.DisplayName()
	}
	return profile.Name
}
