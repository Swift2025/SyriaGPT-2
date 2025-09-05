import { getDictionary } from '../../../../get-dictionary';
import { Locale } from '../../../../i18n-config';
import CheckEmailClient from './CheckEmailClient';

export default async function CheckEmailPage({ params: { lang } }: { params: { lang: Locale } }) {
  const dictionary = await getDictionary(lang);
  return <CheckEmailClient dictionary={dictionary} />;
}
