export interface Resume {
    id: string;
    name: string;
    email: string;
    phone: string;
    skills: string[];
    experience: {
        company: string;
        position: string;
        duration: string;
        description: string;
    }[];
}
