namespace Models {
  export interface User {
    id: string;
  }

  export type Alias = User;
}

interface Local {
  name: string;
}

type LocalAlias = Local;

function use<T extends Local>(value: T): LocalAlias {
  const item: Models.User = value;
  return item as LocalAlias;
}
