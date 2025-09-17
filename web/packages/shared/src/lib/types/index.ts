export type Condition = {
    type: string;
    operator: 'equal' | 'not-equal';
    value?: string;
}

export type Filter = {
    field: string;
    conditions: Condition[];
}